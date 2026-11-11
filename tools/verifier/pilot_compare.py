"""Determinism check and comparator runs for the synthetic compiler-worker pilot.

Inputs are two output directories made by build_pilot.sh (build A and build B) from the same
sources and recipe. Output is metadata only: hashes, counts, field names, reason codes. Byte
context from failing comparisons goes to the comparator's own private diagnostics files.

  determinism: say which bytes differ between the builds and attribute them to named fields.
  compare:     run tools/compare.py on object A against image B for each pilot function,
               plus negative cases that must be rejected.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from pecoff import CoffObject, PeImage  # noqa: E402

FUNCTIONS = ['pilot_mix', 'pilot_field', 'pilot_branch', 'pilot_scale', 'pilot_call']
SOURCE_PATH = 'tools/verifier/synthetic/pilot.cpp'
VARIANT_PATH = 'tools/verifier/synthetic/pilot_variant.cpp'
DEBUG_TYPES = {1: 'COFF', 2: 'CODEVIEW', 4: 'MISC', 12: 'VC_FEATURE', 13: 'POGO', 14: 'ILTCG', 16: 'REPRO',
               20: 'EX_DLLCHARACTERISTICS'}


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def parse_map(path):
    """Return {name: rva} from an MSVC linker map; names listed twice at different RVAs are dropped."""
    text = Path(path).read_text(errors='replace')
    base = int(re.search(r'Preferred load address is ([0-9a-fA-F]+)', text).group(1), 16)
    found, ambiguous = {}, set()
    line_re = re.compile(r'^\s*[0-9a-fA-F]{4}:[0-9a-fA-F]{8}\s+(\S+)\s+([0-9a-fA-F]{16})\b')
    for line in text.splitlines():
        m = line_re.match(line)
        if not m:
            continue
        name, va = m.group(1), int(m.group(2), 16)
        if va < base:
            continue
        rva = va - base
        if name in found and found[name] != rva:
            ambiguous.add(name)
        found.setdefault(name, rva)
    for name in ambiguous:
        del found[name]
    return found, sorted(ambiguous)


def function_section(obj, name):
    for sym in obj.symbols.values():
        if sym.name == name and sym.section > 0:
            return obj.section(sym.section)
    raise SystemExit(f'{name} not defined in object')


def image_bytes(image, rva, size):
    return image.read(rva, size, 'pilot function')[1]


def diff_offsets(a, b):
    return [i for i in range(min(len(a), len(b))) if a[i] != b[i]]


def pe_fields(blob):
    """Named byte ranges in a PE image that are expected to carry build-specific metadata."""
    fields = []
    lfanew = struct.unpack_from('<I', blob, 60)[0]
    fields.append(('COFF header TimeDateStamp', lfanew + 8, 4))
    opt = lfanew + 24
    fields.append(('optional header CheckSum', opt + 64, 4))
    image = PeImage(blob)

    def file_offset(rva):
        sec = image.section_for(rva)
        return sec.raw_ptr + rva - sec.vaddr

    ndirs = struct.unpack_from('<I', blob, opt + 108)[0]
    dirs = [struct.unpack_from('<II', blob, opt + 112 + 8 * i) for i in range(ndirs)]
    if ndirs > 0 and dirs[0][1]:
        fields.append(('export directory TimeDateStamp', file_offset(dirs[0][0]) + 4, 4))
    if ndirs > 6 and dirs[6][1]:
        base = file_offset(dirs[6][0])
        for i in range(dirs[6][1] // 28):
            entry = base + 28 * i
            kind = struct.unpack_from('<I', blob, entry + 12)[0]
            label = DEBUG_TYPES.get(kind, f'type {kind}')
            fields.append((f'debug directory entry {i} ({label}) TimeDateStamp', entry + 4, 4))
            size, _addr, ptr = struct.unpack_from('<III', blob, entry + 16)
            if kind == 2 and blob[ptr:ptr + 4] == b'RSDS':
                fields.append(('CodeView RSDS GUID', ptr + 4, 16))
                fields.append(('CodeView RSDS age', ptr + 20, 4))
                fields.append(('CodeView RSDS PDB path', ptr + 24, size - 24))
            elif size:
                fields.append((f'debug data ({label})', ptr, size))
    return fields, image


def attribute(offsets, fields, sections):
    labels = {}
    for off in offsets:
        name = next((n for n, start, size in fields if start <= off < start + size), None)
        if name is None:
            sec = next((s.name for s in sections if s.raw_ptr <= off < s.raw_ptr + s.raw_size), 'headers')
            name = f'UNEXPLAINED in {sec}'
        labels[name] = labels.get(name, 0) + 1
    return labels


def determinism(a_dir, b_dir):
    a_dir, b_dir = Path(a_dir), Path(b_dir)
    out = {'files': {}}
    for name in ('pilot.obj', 'pilot_variant.obj', 'pilot.dll', 'pilot.pdb', 'pilot.map'):
        a, b = (a_dir / name).read_bytes(), (b_dir / name).read_bytes()
        out['files'][name] = {'identical': a == b, 'size_a': len(a), 'size_b': len(b),
                              'sha256_a': sha256(a), 'sha256_b': sha256(b)}
    for name in ('pilot.obj', 'pilot_variant.obj'):
        a, b = (a_dir / name).read_bytes(), (b_dir / name).read_bytes()
        oa, ob = CoffObject(a), CoffObject(b)
        out['files'][name]['sections_identical'] = all(
            sa.name == sb.name and sa.data == sb.data for sa, sb in zip(oa.sections, ob.sections)) and \
            len(oa.sections) == len(ob.sections)
        fields = [('COFF header TimeDateStamp', 4, 4)]
        out['files'][name]['differing_bytes_by_field'] = attribute(diff_offsets(a, b), fields, oa.sections)
    a, b = (a_dir / 'pilot.dll').read_bytes(), (b_dir / 'pilot.dll').read_bytes()
    fields, ia = pe_fields(a)
    _, ib = pe_fields(b)
    out['files']['pilot.dll']['differing_bytes_by_field'] = attribute(diff_offsets(a, b), fields, ia.sections)
    out['files']['pilot.dll']['sections'] = {
        s.name: {'identical': s.raw_size == t.raw_size and
                 a[s.raw_ptr:s.raw_ptr + s.raw_size] == b[t.raw_ptr:t.raw_ptr + t.raw_size],
                 'sha256_a': sha256(a[s.raw_ptr:s.raw_ptr + s.raw_size])}
        for s, t in zip(ia.sections, ib.sections)}
    ma, mb = (a_dir / 'pilot.map').read_text(errors='replace').splitlines(), \
        (b_dir / 'pilot.map').read_text(errors='replace').splitlines()
    out['files']['pilot.map']['differing_lines'] = [
        re.sub(r'[0-9a-fA-F]{8,}', '<hex>', re.sub(r'\d', '#', x))[:60]
        for x, y in zip(ma, mb) if x != y]
    syms_a, _ = parse_map(a_dir / 'pilot.map')
    syms_b, _ = parse_map(b_dir / 'pilot.map')
    obj_b = CoffObject((b_dir / 'pilot.obj').read_bytes())
    per_function = {}
    for fn in FUNCTIONS:
        size = len(function_section(obj_b, fn).data)
        fa, fb = image_bytes(ia, syms_a[fn], size), image_bytes(ib, syms_b[fn], size)
        per_function[fn] = {'rva_a': syms_a[fn], 'rva_b': syms_b[fn], 'size': size,
                            'identical': fa == fb and syms_a[fn] == syms_b[fn], 'sha256': sha256(fa)}
    out['functions_in_image'] = per_function
    return out


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    return path


def run_case(case, work, a_dir, b_dir, recipe, recipe_sha, manifest, symbols, function, obj_name, source_path):
    case_dir = work / case
    case_dir.mkdir(parents=True, exist_ok=True)
    obj = a_dir / obj_name
    obj_bytes = obj.read_bytes()
    obj_b = CoffObject((b_dir / 'pilot.obj').read_bytes())
    size = len(function_section(obj_b, function).data)
    # The pilot sources are not committed yet, so the source file hash stands in for a revision.
    # Task and build record name the same source, so provenance checks pass and a negative case
    # is decided by the code comparison itself.
    source_sha = sha256((REPO / source_path).read_bytes())
    task = {'task_id': case, 'build_id': manifest['build_id'], 'target_image_sha256': manifest['image_sha256'],
            'rva': symbols['symbols'][function]['rva'], 'size': size, 'symbol': function,
            'source_revision': source_sha, 'source_path': source_path, 'recipe_sha256': recipe_sha}
    build_record = {'source_revision': source_sha, 'source_path': source_path,
                    'recipe_sha256': recipe_sha, 'object_sha256': sha256(obj_bytes)}
    paths = {'task': write_json(case_dir / 'task.json', task),
             'manifest': write_json(case_dir / 'manifest.json', manifest),
             'build-record': write_json(case_dir / 'build-record.json', build_record),
             'symbols': write_json(case_dir / 'symbols.json', symbols)}
    # No -I here: compare.py imports pecoff from its own directory, which isolated mode removes.
    cmd = [sys.executable, str(REPO / 'tools' / 'compare.py'), '--task', str(paths['task']),
           '--manifest', str(paths['manifest']), '--recipe', str(recipe),
           '--build-record', str(paths['build-record']), '--object', str(obj),
           '--image', str(b_dir / 'pilot.dll'), '--symbols', str(paths['symbols']),
           '--report', str(case_dir / 'report.json'), '--diagnostics', str(case_dir / 'diagnostics.json')]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if not (case_dir / 'report.json').exists():
        raise SystemExit(f'{case}: comparator produced no report (exit {proc.returncode}): {proc.stderr[-300:]}')
    report = json.loads((case_dir / 'report.json').read_text())
    return {'case': case, 'function': function, 'object': obj_name, 'exit': proc.returncode,
            'result': report.get('result'), 'reason': report.get('reason'), 'detail': report.get('detail'),
            'coverage': report.get('coverage'), 'stderr': proc.stderr.strip()[:200]}


def compare_all(a_dir, b_dir, work, recipe_path):
    a_dir, b_dir, work = Path(a_dir).resolve(), Path(b_dir).resolve(), Path(work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    recipe_sha = sha256(Path(recipe_path).read_bytes())
    image = (b_dir / 'pilot.dll').read_bytes()
    manifest = {'schema_version': 1, 'status': 'pinned', 'build_id': 'synthetic-boat-pilot-b',
                'image_sha256': sha256(image)}
    found, ambiguous = parse_map(b_dir / 'pilot.map')
    symbols = {'schema': 1, 'build_id': manifest['build_id'],
               'symbols': {name: {'rva': rva, 'size': None} for name, rva in found.items()}, 'folds': []}
    # Task ids must match the contract's [a-z0-9-] pattern, so underscores become hyphens.
    results = [run_case(f'positive-{fn.replace("_", "-")}', work, a_dir, b_dir, recipe_path, recipe_sha, manifest, symbols, fn,
                        'pilot.obj', SOURCE_PATH) for fn in FUNCTIONS]
    results.append(run_case('negative-variant-source', work, a_dir, b_dir, recipe_path, recipe_sha, manifest,
                            symbols, 'pilot_mix', 'pilot_variant.obj', VARIANT_PATH))
    wrong_call = json.loads(json.dumps(symbols))
    wrong_call['symbols']['pilot_scale']['rva'] = symbols['symbols']['pilot_mix']['rva']
    results.append(run_case('negative-wrong-call-target', work, a_dir, b_dir, recipe_path, recipe_sha, manifest,
                            wrong_call, 'pilot_call', 'pilot.obj', SOURCE_PATH))
    data_names = [n for n in found if 'g_pilot_total' in n]
    if data_names:
        wrong_data = json.loads(json.dumps(symbols))
        wrong_data['symbols'][data_names[0]]['rva'] += 8
        results.append(run_case('negative-wrong-data-target', work, a_dir, b_dir, recipe_path, recipe_sha,
                                manifest, wrong_data, 'pilot_scale', 'pilot.obj', SOURCE_PATH))
    return {'image_b_sha256': manifest['image_sha256'], 'map_symbols': len(found),
            'map_ambiguous_names': len(ambiguous), 'data_symbol_names': data_names, 'cases': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('determinism')
    d.add_argument('a')
    d.add_argument('b')
    c = sub.add_parser('compare')
    c.add_argument('a')
    c.add_argument('b')
    c.add_argument('--work', required=True, help='Private directory for tasks, reports and diagnostics')
    c.add_argument('--recipe', required=True)
    args = parser.parse_args()
    if args.cmd == 'determinism':
        result = determinism(args.a, args.b)
    else:
        result = compare_all(args.a, args.b, args.work, args.recipe)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
