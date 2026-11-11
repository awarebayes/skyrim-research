"""Comparator v2 validation on real MSVC output of original synthetic sources.

Input: an output directory of build_eh.sh (eh_cases.obj, eh_gs.obj, eh.dll, eh.map). For every
exported function in either object, compare the object against the DLL with a symbol map parsed
from the linker map (positive cases), then run negative cases on altered copies of the image or
the map. Output is metadata only: function names of the synthetic sources, result and reason
codes, coverage counts. Run it on the verifier host or locally on fetched outputs; it reads no
game data.

    python3 tools/verifier/eh_compare.py <build-dir> [--work .local/<dir>]
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

REPO = Path(__file__).resolve().parents[1].parent
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare import compare  # noqa: E402
from pecoff import CoffObject, PeImage, STORAGE_EXTERNAL  # noqa: E402
from pilot_compare import parse_map  # noqa: E402

OBJECTS = {'eh_cases.obj': 'tools/verifier/synthetic/eh_cases.cpp', 'eh_gs.obj': 'tools/verifier/synthetic/eh_gs.cpp'}


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def exported_functions(obj):
    """External function symbols at offset 0 of their own code section, as /Gy emits them."""
    found = []
    for sym in obj.symbols.values():
        if sym.section > 0 and sym.storage == STORAGE_EXTERNAL and sym.is_function and sym.value == 0:
            sec = obj.section(sym.section)
            if sec.name.startswith('.text'):
                found.append((sym.name, len(sec.data)))
    return sorted(found)


def run(name, obj_bytes, image_bytes, symbols, source_path, size, build_id='synthetic-eh'):
    recipe = json.dumps({'compiler': {'binary_sha256': '0' * 64, 'version': 'see pinned.sha256'},
                         'flags': ['see flags.txt']}).encode()
    revision = sha256((REPO / source_path).read_bytes())
    task = {'task_id': 'eh-' + hashlib.sha1(name.encode()).hexdigest()[:10], 'build_id': build_id,
            'target_image_sha256': sha256(image_bytes), 'rva': symbols[name]['rva'], 'size': size, 'symbol': name,
            'source_revision': revision, 'source_path': source_path, 'recipe_sha256': sha256(recipe)}
    return compare(task, {'status': 'pinned', 'build_id': build_id, 'image_sha256': sha256(image_bytes)}, recipe,
                   {'source_revision': revision, 'source_path': source_path, 'recipe_sha256': sha256(recipe),
                    'object_sha256': sha256(obj_bytes)}, obj_bytes, image_bytes,
                   {'schema': 1, 'build_id': build_id, 'symbols': symbols, 'folds': []})


def summary(case, name, report):
    cov = report.get('coverage') or {}
    eh = cov.get('eh') or {}
    return {'case': case, 'function': name, 'result': report['result'], 'reason': report['reason'],
            'detail': report['detail'] if report['result'] != 'pass' else None,
            'code': [cov.get('code_bytes_total'), cov.get('code_bytes_exact'), cov.get('code_bytes_by_reference')],
            'funclets': [cov.get('funclet_sections'), cov.get('funclet_bytes_total')],
            'unwind': [cov.get('unwind'), cov.get('unwind_entries'), cov.get('unwind_chained_entries')],
            'self_rva_fields': cov.get('self_rva_fields'), 'handlers': eh.get('handlers'),
            'structures': eh.get('structures'), 'type_names': eh.get('type_names_compared')}


class Target:
    """Independent reader of the linked DLL's EH data, used only to place negative-case edits."""

    def __init__(self, blob):
        self.blob, self.image = bytearray(blob), PeImage(blob)
        self.pdata = {b: (e, u) for b, e, u in self.image.runtime_functions()}

    def offset(self, rva):
        sec = self.image.section_for(rva)
        return sec.raw_ptr + rva - sec.vaddr

    def u32(self, rva):
        return struct.unpack_from('<I', self.blob, self.offset(rva))[0]

    def put(self, rva, value):
        struct.pack_into('<I', self.blob, self.offset(rva), value)

    def handler_data(self, func_rva):
        unwind = self.pdata[func_rva][1]
        count = self.blob[self.offset(unwind) + 2]
        return unwind + 4 + 2 * (count + (count & 1)) + 4

    def funcinfo(self, func_rva):
        return self.u32(self.handler_data(func_rva))


def negatives(objs, image, symbols):
    results = []
    by_name = {name: (obj_name, size) for obj_name, (_b, funcs) in objs.items() for name, size in funcs}

    def case(label, name, image_bytes=None, symbol_map=None, size=None):
        obj_name, real_size = by_name[name]
        report = run(name, objs[obj_name][0], image_bytes or image, symbol_map or symbols, OBJECTS[obj_name],
                     size or real_size)
        results.append(summary(label, name, report))

    catching = next(n for n in by_name if n.startswith('?eh_catching@'))
    guarded = next(n for n in by_name if n.startswith('?eh_guarded@'))
    switch = next(n for n in by_name if n.startswith('?eh_switch@'))
    chained = next(n for n in by_name if n.startswith('?eh_chained@'))
    seh = next(n for n in by_name if n.startswith('?eh_seh_always@'))
    fn = symbols[catching]['rva']

    wrong = json.loads(json.dumps(symbols))
    wrong['__CxxFrameHandler3']['rva'] = symbols['__C_specific_handler']['rva']
    case('negative-wrong-handler', catching, symbol_map=wrong)

    wrong = json.loads(json.dumps(symbols))
    wrong['??_R0?AUEhError@@@8']['rva'] = symbols['??_R0?AUEhOtherError@@@8']['rva']
    case('negative-wrong-catch-type', catching, symbol_map=wrong)

    t = Target(image)
    info = t.funcinfo(fn)
    ip_map, n_ip = t.u32(info + 24), t.u32(info + 20)
    t.put(ip_map + 8 * (n_ip - 1) + 4, t.u32(ip_map + 8 * (n_ip - 1) + 4) + 1)
    case('negative-ip-to-state-state', catching, bytes(t.blob))

    t = Target(image)
    info = t.funcinfo(fn)
    handlers = t.u32(t.u32(info + 16) + 16)
    funclet = t.u32(handlers + 12)
    t.blob[t.offset(funclet) + 6] ^= 0x01
    case('negative-funclet-byte', catching, bytes(t.blob))

    t = Target(image)
    info = t.funcinfo(symbols[guarded]['rva'])
    t.put(t.u32(info + 8) + 4, 0)
    case('negative-missing-unwind-funclet', guarded, bytes(t.blob))

    t = Target(image)
    info = t.funcinfo(fn)
    try_map = t.u32(info + 16)
    t.put(try_map + 8, t.u32(try_map + 8) + 1)
    case('negative-try-catch-high', catching, bytes(t.blob))

    t = Target(image)
    sw = symbols[switch]['rva']
    obj_name, size = by_name[switch]
    table = next(off for off in range(0, size - 8, 4) if t.u32(sw + off) - sw in range(size)
                 and t.u32(sw + off + 4) - sw in range(size) and t.u32(sw + off + 8) - sw in range(size)
                 and off > 16)
    first, second = t.u32(sw + table), t.u32(sw + table + 4)
    t.put(sw + table, second)
    t.put(sw + table + 4, first)
    case('negative-jump-table-entry', switch, bytes(t.blob))

    t = Target(image)
    ch = symbols[chained]['rva']
    entries = sorted((b, e, u) for b, (e, u) in t.pdata.items() if ch <= b < ch + by_name[chained][1])
    last_begin, _end, last_unwind = entries[-1]
    count = t.blob[t.offset(last_unwind) + 2]
    parent = last_unwind + 4 + 2 * (count + (count & 1))
    other = next(e for e in entries if e[0] != t.u32(parent) and e[0] != last_begin)
    t.put(parent, other[0])
    t.put(parent + 4, other[1])
    case('negative-wrong-chained-parent', chained, bytes(t.blob))
    case('negative-primary-entry-size', chained, size=entries[0][1] - entries[0][0])

    t = Target(image)
    scope = t.handler_data(symbols[seh]['rva'])
    t.put(scope + 4 + 8, 0)
    case('negative-scope-constant', seh, bytes(t.blob))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build')
    args = parser.parse_args()
    build = Path(args.build)
    image = (build / 'eh.dll').read_bytes()
    found, ambiguous = parse_map(build / 'eh.map')
    # A symbol map for a real target names functions and data, not compiler-local labels,
    # funclets or EH tables (all spelled with '$'); funclets are found through the EH data.
    symbols = {name: {'rva': rva, 'size': None} for name, rva in found.items() if '$' not in name}
    objs = {}
    for obj_name in OBJECTS:
        blob = (build / obj_name).read_bytes()
        objs[obj_name] = (blob, exported_functions(CoffObject(blob)))
    positives = []
    for obj_name, (blob, funcs) in objs.items():
        for name, size in funcs:
            if name not in symbols:
                positives.append({'case': 'positive', 'function': name, 'result': 'not-in-image'})
                continue
            positives.append(summary('positive', name, run(name, blob, image, symbols, OBJECTS[obj_name], size)))
    out = {'image_sha256': sha256(image), 'map_symbols': len(found), 'map_ambiguous': len(ambiguous),
           'positives': positives, 'negatives': negatives(objs, image, symbols)}
    print(json.dumps(out, indent=1, sort_keys=True))
    bad = [c for c in out['positives'] if c['result'] not in ('pass', 'not-in-image')] + [c for c in out['negatives'] if c['result'] == 'pass']
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
