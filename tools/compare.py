"""Compare one compiled candidate function with a pinned target image range (contract v1).

Implements docs/comparator-contract.md. The public report holds metadata, hashes and a result
code only; byte-level context is written solely to an optional diagnostics file under .local/.
A `pass` here is evidence for review, not acceptance: it never sets a function to `matched`.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from pecoff import (RUNTIME_FUNCTION_SIZE, SCN_CNT_CODE, SCN_MEM_EXECUTE, STORAGE_EXTERNAL, SYM_ABSOLUTE,
                    SYM_DEBUG, SYM_UNDEFINED, CoffObject, PeImage, Reject, rel_name, unwind_info_length)

ROOT = Path(__file__).resolve().parents[1]
COMPARATOR_VERSION = '0.1.0'
CONTRACT_VERSION = 1
REPORT_SCHEMA = 1
SHA256 = re.compile(r'[0-9a-f]{64}')
IDENT = re.compile(r'[a-z0-9][a-z0-9-]*')
# Hex runs this long in a non-hash field would most likely be leaked bytes, so they are refused.
HEX_RUN = re.compile(r'[0-9a-fA-F]{16,}')
HASH_KEYS = {'image_sha256', 'expected_image_sha256', 'object_sha256', 'recipe_sha256',
             'compiler_binary_sha256', 'source_sha256', 'source_revision'}

# Displacement relocations: field is a signed 32-bit offset from the end of the instruction,
# which ends `k` bytes after the 4-byte field (an immediate operand follows for k > 0).
REL32_TAIL = {0x04: 0, 0x05: 1, 0x06: 2, 0x07: 3, 0x08: 4, 0x09: 5}
ADDR32NB = 0x03
SUPPORTED_RELOCATIONS = set(REL32_TAIL) | {ADDR32NB}


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def comparator_source_sha256():
    digest = hashlib.sha256()
    for name in ('compare.py', 'pecoff.py'):
        digest.update(name.encode() + b'\0' + (Path(__file__).with_name(name)).read_bytes())
    return digest.hexdigest()


def need(condition, reason, detail):
    if not condition:
        raise Reject(reason, detail)


def field(mapping, key, check, reason, what):
    value = mapping.get(key) if isinstance(mapping, dict) else None
    need(check(value), reason, f'{what} field {key!r} is missing or invalid')
    return value


def is_text(value):
    return isinstance(value, str) and bool(value.strip())


def is_uint(value):
    return type(value) is int and value >= 0


def is_hash(value):
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def check_task(task):
    field(task, 'task_id', lambda v: isinstance(v, str) and IDENT.fullmatch(v), 'invalid-task', 'task')
    field(task, 'build_id', lambda v: isinstance(v, str) and IDENT.fullmatch(v), 'invalid-task', 'task')
    for key in ('target_image_sha256', 'recipe_sha256'):
        field(task, key, is_hash, 'invalid-task', 'task')
    field(task, 'rva', is_uint, 'invalid-task', 'task')
    field(task, 'size', lambda v: is_uint(v) and v > 0, 'invalid-task', 'task')
    for key in ('symbol', 'source_revision', 'source_path'):
        field(task, key, is_text, 'invalid-task', 'task')


def check_provenance(task, manifest, recipe_bytes, build_record, object_bytes, image_bytes):
    """Every pinned input must be the one the task names before any bytes are compared."""
    need(isinstance(manifest, dict) and manifest.get('status') == 'pinned', 'target-unpinned',
         'target manifest is not pinned')
    need(manifest.get('build_id') == task['build_id'], 'manifest-mismatch', 'task build id differs from manifest')
    need(manifest.get('image_sha256') == task['target_image_sha256'], 'manifest-mismatch',
         'task image hash differs from manifest')
    need(sha256(recipe_bytes) == task['recipe_sha256'], 'stale-recipe',
         'recipe file hash differs from the recipe the task pins')
    try:
        recipe = json.loads(recipe_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise Reject('invalid-recipe', 'recipe is not JSON') from None
    compiler = field(recipe, 'compiler', lambda v: isinstance(v, dict), 'invalid-recipe', 'recipe')
    field(compiler, 'binary_sha256', is_hash, 'invalid-recipe', 'recipe compiler')
    field(compiler, 'version', is_text, 'invalid-recipe', 'recipe compiler')
    field(recipe, 'flags', lambda v: isinstance(v, list) and all(is_text(f) for f in v), 'invalid-recipe', 'recipe')
    need(isinstance(build_record, dict), 'invalid-build-record', 'build record is not an object')
    need(build_record.get('source_revision') == task['source_revision'], 'stale-source-revision',
         'candidate was built from a different source revision than the task pins')
    need(build_record.get('source_path') == task['source_path'], 'source-path-mismatch',
         'candidate was built from a different source path than the task pins')
    need(build_record.get('recipe_sha256') == task['recipe_sha256'], 'stale-recipe',
         'candidate was built with a different recipe than the task pins')
    need(build_record.get('object_sha256') == sha256(object_bytes), 'object-provenance-mismatch',
         'candidate object hash differs from its build record')
    need(sha256(image_bytes) == task['target_image_sha256'], 'image-hash-mismatch',
         'target image hash differs from the pinned hash')
    return recipe


def load_symbol_map(task, symbol_map):
    need(isinstance(symbol_map, dict) and symbol_map.get('schema') == 1, 'invalid-symbol-map',
         'symbol map schema must be 1')
    need(symbol_map.get('build_id') == task['build_id'], 'symbol-map-build-mismatch',
         'symbol map belongs to another build')
    entries = symbol_map.get('symbols')
    need(isinstance(entries, dict), 'invalid-symbol-map', 'symbols must be an object')
    for name, entry in entries.items():
        need(isinstance(entry, dict) and is_uint(entry.get('rva')), 'invalid-symbol-map', 'entry needs an rva')
        need(entry.get('size') is None or (is_uint(entry['size']) and entry['size'] > 0), 'invalid-symbol-map',
             'entry size must be null or positive')
    folds = symbol_map.get('folds', [])
    need(isinstance(folds, list) and all(isinstance(g, list) and len(g) > 1 and all(n in entries for n in g)
                                         for g in folds), 'invalid-symbol-map', 'folds must list known symbols')
    for group in folds:
        need(len({entries[n]['rva'] for n in group}) == 1, 'invalid-symbol-map', 'folded symbols differ in RVA')
    return entries, [set(g) for g in folds]


def check_placement(task, entries, folds):
    """Reject symbol maps that alias or overlap the target range in ways not explicitly declared."""
    start, end, symbol = task['rva'], task['rva'] + task['size'], task['symbol']
    if symbol in entries:
        need(entries[symbol]['rva'] == start, 'symbol-map-conflict', 'symbol map places the function elsewhere')
        need(entries[symbol].get('size') in (None, task['size']), 'symbol-map-conflict',
             'symbol map gives the function another size')
    declared = set().union(*(g for g in folds if symbol in g)) if folds else set()
    aliases = []
    for name, entry in entries.items():
        if name == symbol:
            continue
        rva, size = entry['rva'], entry.get('size')
        if rva == start:
            need(name in declared, 'undeclared-alias', 'another symbol shares the function RVA without a fold entry')
            aliases.append(name)
            continue
        overlaps = start < rva < end or (size is not None and rva < end and start < rva + size)
        need(not overlaps, 'overlapping-function', 'another symbol range overlaps the function range')
    return sorted(aliases)


def find_function(obj, name):
    matches = [s for s in obj.symbols.values() if s.name == name and s.section > 0]
    need(matches, 'function-symbol-missing', 'candidate object does not define the task symbol')
    need(len(matches) == 1, 'function-symbol-ambiguous', 'candidate object defines the task symbol twice')
    sym = matches[0]
    need(sym.storage == STORAGE_EXTERNAL, 'candidate-boundary-unsupported', 'task symbol is not external')
    sec = obj.section(sym.section)
    need(sec.flags & SCN_CNT_CODE and sec.data is not None, 'candidate-boundary-unsupported',
         'task symbol is not in an initialized code section')
    need(sym.value == 0, 'candidate-boundary-unsupported', 'function does not start its section')
    others = [s for s in obj.symbols.values() if s.section == sym.section and s.value != 0
              and (s.storage == STORAGE_EXTERNAL or s.is_function)]
    # Contract v1 takes the section end as the function end, which is sound only for one function per section.
    need(not others, 'candidate-boundary-unsupported', 'code section holds more than one function')
    return sym, sec


def resolve(sym, func_sec, task, entries):
    if sym.section == func_sec.index:
        return task['rva'] + sym.value
    need(sym.section not in (SYM_ABSOLUTE, SYM_DEBUG), 'unsupported-relocation',
         'relocation targets an absolute or debug symbol')
    need(sym.name in entries, 'unresolved-symbol', f'no target RVA for referenced symbol {sym.name!r}')
    return entries[sym.name]['rva']


def check_relocation_layout(sec, size, what):
    spans = []
    for rel in sorted(sec.relocs, key=lambda r: r.offset):
        need(rel.kind in SUPPORTED_RELOCATIONS, 'unsupported-relocation',
             f'{what} uses relocation {rel_name(rel.kind)} at +0x{rel.offset:x}')
        need(rel.offset + 4 <= size, 'malformed-relocation', f'{what} relocation at +0x{rel.offset:x} is out of range')
        need(not spans or spans[-1][1] <= rel.offset, 'malformed-relocation', f'{what} relocations overlap')
        spans.append((rel.offset, rel.offset + 4, rel))
    return spans


def expected_field(rel, addend_bytes, target_rva, place_rva):
    if rel.kind == ADDR32NB:
        value = target_rva + struct.unpack('<I', addend_bytes)[0]
        need(value <= 0xFFFFFFFF, 'relocation-overflow', f'ADDR32NB at +0x{rel.offset:x} overflows')
        return struct.pack('<I', value)
    value = target_rva + struct.unpack('<i', addend_bytes)[0] - (place_rva + 4 + REL32_TAIL[rel.kind])
    need(-2**31 <= value < 2**31, 'relocation-overflow', f'{rel_name(rel.kind)} at +0x{rel.offset:x} overflows')
    return struct.pack('<i', value)


def compare_code(obj, sec, task, entries, target, coverage):
    candidate = sec.data
    spans = check_relocation_layout(sec, len(candidate), 'function')
    position = 0
    for start, end, rel in spans + [(len(candidate), len(candidate), None)]:
        for offset in range(position, start):
            if candidate[offset] != target[offset]:
                raise Reject('code-byte-mismatch', f'code differs at +0x{offset:x}',
                             raw={'offset': offset, 'candidate': candidate[max(0, offset - 8):offset + 8].hex(),
                                  'target': target[max(0, offset - 8):offset + 8].hex()})
        coverage['code_bytes_exact'] += start - position
        if rel is None:
            break
        ref = obj.symbols[rel.symbol]
        want = expected_field(rel, candidate[start:end], resolve(ref, sec, task, entries), task['rva'] + start)
        if want != target[start:end]:
            raise Reject('relocation-target-mismatch',
                         f'{rel_name(rel.kind)} at +0x{start:x} does not encode the RVA of {ref.name!r}',
                         raw={'offset': start, 'expected_field': want.hex(), 'target_field': target[start:end].hex()})
        coverage['code_bytes_by_reference'] += 4
        kinds = coverage['relocations_by_type']
        kinds[rel_name(rel.kind)] = kinds.get(rel_name(rel.kind), 0) + 1
        position = end


def candidate_unwind(obj, func_sec):
    """Collect (begin, end, unwind bytes) for .pdata entries whose begin lies in the function section."""
    found = []
    for pdata in (s for s in obj.sections if s.name == '.pdata'):
        need(pdata.data is not None and len(pdata.data) % RUNTIME_FUNCTION_SIZE == 0, 'malformed-pdata',
             'candidate .pdata size is not a multiple of 12')
        by_offset = {r.offset: r for r in pdata.relocs}
        need(all(r.kind == ADDR32NB for r in pdata.relocs), 'unsupported-relocation',
             'candidate .pdata uses a relocation other than ADDR32NB')
        for base in range(0, len(pdata.data), RUNTIME_FUNCTION_SIZE):
            need(all(base + k in by_offset for k in (0, 4, 8)), 'malformed-pdata',
                 'candidate .pdata entry is not fully relocated')
            refs = [obj.symbols[by_offset[base + k].symbol] for k in (0, 4, 8)]
            addends = struct.unpack_from('<III', pdata.data, base)
            if refs[0].section != func_sec.index:
                continue
            need(refs[1].section == func_sec.index, 'malformed-pdata', 'candidate .pdata entry ends in another section')
            need(refs[2].section > 0, 'malformed-pdata', 'candidate unwind info symbol is undefined')
            xdata = obj.section(refs[2].section)
            need(xdata.data is not None, 'malformed-pdata', 'candidate unwind info section has no data')
            at = refs[2].value + addends[2]
            length = unwind_info_length(xdata.data[at:at + 4], 'candidate unwind info')
            need(at + length <= len(xdata.data), 'truncated-input', 'candidate unwind info is truncated')
            need(not any(at <= r.offset < at + length for r in xdata.relocs), 'unsupported-relocation',
                 'candidate unwind info contains a relocation')
            found.append((refs[0].value + addends[0], refs[1].value + addends[1], xdata.data[at:at + length]))
    return sorted(found)


def compare_unwind(obj, sec, task, image, coverage):
    start, end = task['rva'], task['rva'] + task['size']
    target_entries = []
    for begin, finish, unwind in image.runtime_functions():
        if begin < end and finish > start:
            need(start <= begin and finish <= end, 'unwind-entry-crosses-boundary',
                 'a target .pdata entry extends beyond the function range')
            target_entries.append((begin - start, finish - start, unwind))
    target_entries.sort()
    candidate_entries = candidate_unwind(obj, sec)
    for begin, finish, _ in candidate_entries:
        need(0 <= begin < finish <= task['size'], 'malformed-pdata', 'candidate .pdata entry is outside the function')
    target_spans = [(b, f) for b, f, _ in target_entries]
    candidate_spans = [(b, f) for b, f, _ in candidate_entries]
    missing = [s for s in target_spans if s not in candidate_spans]
    extra = [s for s in candidate_spans if s not in target_spans]
    need(not missing, 'unwind-coverage-missing',
         f'{len(missing)} target .pdata entr(y/ies) in the range have no candidate counterpart')
    need(not extra, 'unwind-coverage-extra', f'{len(extra)} candidate .pdata entr(y/ies) are absent from the target')
    for (begin, _, unwind_rva), (_, _, info) in zip(target_entries, candidate_entries):
        _, header = image.read(unwind_rva, 4, 'target unwind info')
        length = unwind_info_length(header, 'target unwind info')
        _, actual = image.read(unwind_rva, length, 'target unwind info')
        if actual != info:
            raise Reject('unwind-info-mismatch', f'unwind info differs for the entry at +0x{begin:x}',
                         raw={'entry': begin, 'candidate': info.hex(), 'target': actual.hex()})
        coverage['unwind_bytes_exact'] += length
    coverage['unwind_entries'] = len(target_entries)
    coverage['unwind'] = 'covered' if target_entries else 'none-in-range'


def sanitized(report):
    """Raise if any report string looks like leaked bytes; hashes are allowed only in hash fields."""
    def walk(value, key=''):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
        elif isinstance(value, list):
            for v in value:
                walk(v, key)
        elif isinstance(value, (bytes, bytearray)):
            raise ValueError(f'report field {key!r} holds raw bytes')
        elif isinstance(value, str):
            if key in HASH_KEYS:
                return
            if HEX_RUN.search(value):
                raise ValueError(f'report field {key!r} holds a long hex run')
    walk(report)
    return report


def write_diagnostics(path, private_root, report, raw):
    path, private_root = Path(path).resolve(), Path(private_root).resolve()
    if private_root not in path.parents:
        raise Reject('diagnostics-path-not-private', 'diagnostics must be written under the private root')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'report': report, 'raw': raw}, indent=2) + '\n')


def compare(task, manifest, recipe_bytes, build_record, object_bytes, image_bytes, symbol_map,
            diagnostics=None, private_root=ROOT / '.local'):
    """Return a sanitized report dict. Never raises for comparison failures; they become `fail`."""
    coverage = {'code_bytes_total': None, 'code_bytes_exact': 0, 'code_bytes_by_reference': 0,
                'relocations_by_type': {}, 'unwind_entries': 0, 'unwind_bytes_exact': 0, 'unwind': 'not-checked',
                'aliases_declared': []}
    report = {'report_schema': REPORT_SCHEMA, 'contract_version': CONTRACT_VERSION,
              'comparator': {'version': COMPARATOR_VERSION, 'source_sha256': comparator_source_sha256()},
              'acceptance': 'not-evaluated', 'result': 'fail', 'reason': None, 'detail': None}
    raw = {}
    try:
        check_task(task)
        report.update(task_id=task['task_id'],
                      function={'build_id': task['build_id'], 'rva': task['rva'], 'size': task['size'],
                                'symbol': task['symbol']},
                      source={'source_revision': task['source_revision'], 'path': task['source_path']},
                      target={'expected_image_sha256': task['target_image_sha256'],
                              'image_sha256': sha256(image_bytes)},
                      candidate={'object_sha256': sha256(object_bytes)})
        recipe = check_provenance(task, manifest, recipe_bytes, build_record, object_bytes, image_bytes)
        report['recipe'] = {'recipe_sha256': task['recipe_sha256'],
                            'compiler_binary_sha256': recipe['compiler']['binary_sha256'],
                            'compiler_version': recipe['compiler']['version'], 'flags': recipe['flags']}
        entries, folds = load_symbol_map(task, symbol_map)
        coverage['aliases_declared'] = check_placement(task, entries, folds)
        obj, image = CoffObject(object_bytes), PeImage(image_bytes)
        _, sec = find_function(obj, task['symbol'])
        need(len(sec.data) == task['size'], 'function-size-mismatch',
             f'candidate function is {len(sec.data)} bytes; task range is {task["size"]} bytes')
        target_sec, target = image.read(task['rva'], task['size'], 'target function range')
        need(target_sec.flags & SCN_MEM_EXECUTE, 'target-not-code', 'target range is not in an executable section')
        coverage['code_bytes_total'] = task['size']
        check_relocation_layout(sec, len(sec.data), 'function')
        compare_code(obj, sec, task, entries, target, coverage)
        compare_unwind(obj, sec, task, image, coverage)
        need(coverage['code_bytes_exact'] + coverage['code_bytes_by_reference'] == task['size'], 'coverage-gap',
             'not every function byte was compared')
        report.update(result='pass', reason='all-checks-passed', detail='all contract v1 checks passed')
    except Reject as exc:
        report.update(reason=exc.reason, detail=exc.detail)
        raw = exc.raw
    report['coverage'] = coverage
    sanitized(report)
    if diagnostics is not None:
        write_diagnostics(diagnostics, private_root, report, raw)
    return report


def load_json(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True, type=Path, help='Task JSON pinning function, source and recipe')
    parser.add_argument('--manifest', default=ROOT / 'builds/target.json', type=Path)
    parser.add_argument('--recipe', required=True, type=Path)
    parser.add_argument('--build-record', required=True, type=Path)
    parser.add_argument('--object', required=True, type=Path, help='Candidate COFF object')
    parser.add_argument('--image', required=True, type=Path, help='Pinned target PE32+ image')
    parser.add_argument('--symbols', required=True, type=Path, help='Symbol-to-RVA map for the target build')
    parser.add_argument('--report', type=Path, help='Write the sanitized report here instead of stdout')
    parser.add_argument('--diagnostics', type=Path, help='Private diagnostics path; must be under .local/')
    args = parser.parse_args()
    try:
        report = compare(load_json(args.task), load_json(args.manifest), args.recipe.read_bytes(),
                         load_json(args.build_record), args.object.read_bytes(), args.image.read_bytes(),
                         load_json(args.symbols), diagnostics=args.diagnostics)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f'FAIL: cannot read inputs: {exc}', file=sys.stderr)
        return 2
    except Reject as exc:
        print(f'FAIL: {exc.reason}: {exc.detail}', file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.report:
        args.report.write_text(text)
    else:
        sys.stdout.write(text)
    return 0 if report['result'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
