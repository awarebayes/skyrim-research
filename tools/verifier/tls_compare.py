"""Comparator thread-local rules on real MSVC output of original synthetic sources.

Input: an output directory of build_tls.sh (tls_cases.obj, tls_variant.obj, tls.dll, tls.map).
Every exported function of tls_cases.obj is compared against the DLL with a symbol map parsed
from the linker map, in which names inside the DLL's TLS template become thread-local entries
(offset from the template start the TLS directory names). Then the perturbed object
tls_variant.obj and altered copies of the map or image must fail. Output is metadata only:
synthetic function names, result and reason codes, coverage counts. Reads no game data.

    python3 tools/verifier/tls_compare.py <build-dir>
"""
import argparse
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eh_compare import exported_functions, run, sha256  # noqa: E402
from pecoff import CoffObject, PeImage, TLS_DIRECTORY  # noqa: E402
from pilot_compare import parse_map  # noqa: E402

SOURCES = {'tls_cases.obj': 'tools/verifier/synthetic/tls_cases.cpp',
           'tls_variant.obj': 'tools/verifier/synthetic/tls_variant.cpp'}
BUILD_ID = 'synthetic-tls'
COUNTER = '?tls_counter@@3HA'


def summary(case, name, report):
    cov = report.get('coverage') or {}
    return {'case': case, 'function': name, 'result': report['result'], 'reason': report['reason'],
            'detail': report['detail'] if report['result'] != 'pass' else None,
            'code': [cov.get('code_bytes_total'), cov.get('code_bytes_exact'), cov.get('code_bytes_by_reference')],
            'relocations': cov.get('relocations_by_type'), 'funclets': cov.get('funclet_sections'),
            'unwind': cov.get('unwind'), 'handlers': (cov.get('eh') or {}).get('handlers')}


def tls_map(found, template):
    """Linker-map names as map entries: inside the TLS template thread-local, elsewhere RVAs."""
    start, end, _index = template
    symbols = {}
    for name, rva in found.items():
        # Compiler-local labels, funclets and EH tables are spelled with '$' and are found through
        # the EH data; a thread-safe static's guard (`?$TSS0@...`) is real data the code references.
        if '$' in name and not name.startswith('?$TSS'):
            continue
        if start <= rva < end:
            symbols[name] = {'kind': 'thread-local', 'tls_offset': rva - start, 'size': None}
        else:
            symbols[name] = {'rva': rva, 'size': None}
    return symbols


def tls_directory_offset(blob):
    """File offset of the TLS data-directory entry, and of the directory itself."""
    lfanew = struct.unpack_from('<I', blob, 60)[0]
    entry = lfanew + 24 + 112 + 8 * TLS_DIRECTORY
    image = PeImage(bytes(blob))
    rva = struct.unpack_from('<I', blob, entry)[0]
    sec = image.section_for(rva)
    return entry, sec.raw_ptr + rva - sec.vaddr


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build')
    args = parser.parse_args()
    build = Path(args.build)
    dll = (build / 'tls.dll').read_bytes()
    image = PeImage(dll)
    template = image.tls_template()
    found, ambiguous = parse_map(build / 'tls.map')
    symbols = tls_map(found, template)
    objs = {name: (build / name).read_bytes() for name in SOURCES}
    funcs = {name: dict(exported_functions(CoffObject(blob))) for name, blob in objs.items()}

    def case(label, obj_name, name, image_bytes=None, symbol_map=None):
        if name not in symbols:
            return {'case': label, 'function': name, 'result': 'not-in-image'}
        report = run(name, objs[obj_name], image_bytes or dll, symbol_map or symbols, SOURCES[obj_name],
                     funcs[obj_name][name], build_id=BUILD_ID)
        return summary(label, name, report)

    def altered(**changes):
        out = json.loads(json.dumps(symbols))
        for name, entry in changes.items():
            if entry is None:
                out.pop(name, None)
            else:
                out[name] = entry
        return out

    # The synthetic subject is the tls_ functions; the library inlines around them (std::exception
    # members, ICF-folded deleting destructors) are eh_compare.py's business.
    positives = [case('positive', 'tls_cases.obj', name) for name in sorted(funcs['tls_cases.obj'])
                 if name.startswith('tls_')]
    no_index = altered(_tls_index=None)
    positives.append(case('positive-no-tls-index-entry', 'tls_cases.obj', 'tls_read_counter', symbol_map=no_index))

    counter = symbols.get(COUNTER, {})
    offset = counter.get('tls_offset', 0)
    negatives = [case('negative-variant-object', 'tls_variant.obj', name) for name in sorted(funcs['tls_variant.obj'])]
    negatives += [
        case('negative-wrong-offset', 'tls_cases.obj', 'tls_read_counter',
             symbol_map=altered(**{COUNTER: {'kind': 'thread-local', 'tls_offset': offset + 4, 'size': None}})),
        case('negative-offset-outside-template', 'tls_cases.obj', 'tls_read_counter',
             symbol_map=altered(**{COUNTER: {'kind': 'thread-local', 'tls_offset': template[1] - template[0],
                                             'size': None}})),
        case('negative-missing-entry', 'tls_cases.obj', 'tls_read_counter', symbol_map=altered(**{COUNTER: None})),
        case('negative-mapped-as-rva', 'tls_cases.obj', 'tls_read_counter',
             symbol_map=altered(**{COUNTER: {'rva': template[0] + offset, 'size': None}})),
        case('negative-tls-index-entry-elsewhere', 'tls_cases.obj', 'tls_read_counter',
             symbol_map=altered(_tls_index={'rva': template[2] + 8, 'size': None})),
    ]
    entry, directory = tls_directory_offset(dll)
    moved = bytearray(dll)
    struct.pack_into('<Q', moved, directory + 16, struct.unpack_from('<Q', moved, directory + 16)[0] + 8)
    negatives.append(case('negative-directory-index-elsewhere', 'tls_cases.obj', 'tls_read_counter',
                          bytes(moved), symbol_map=no_index))
    missing = bytearray(dll)
    struct.pack_into('<II', missing, entry, 0, 0)
    negatives.append(case('negative-no-tls-directory', 'tls_cases.obj', 'tls_read_counter', bytes(missing)))

    out = {'image_sha256': sha256(dll), 'map_symbols': len(found), 'map_ambiguous': len(ambiguous),
           'tls_template_starts_section': template[0] == image.section_for(template[0]).vaddr,
           'tls_template_section': image.section_for(template[0]).name,
           'tls_template_size': template[1] - template[0],
           'thread_local_entries': sorted(n for n, e in symbols.items() if e.get('kind') == 'thread-local'),
           'positives': positives, 'negatives': negatives}
    print(json.dumps(out, indent=1, sort_keys=True))
    bad = [c for c in positives if c['result'] not in ('pass', 'not-in-image')]
    bad += [c for c in negatives if c['result'] != 'fail']
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
