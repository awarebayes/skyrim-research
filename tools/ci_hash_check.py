#!/usr/bin/env python3
"""Public-only MSVC self-test. No target image, target-hash generator or acceptance output.

The three references are existing accepted records, including contrib.py's setup self-test.
Use the comparator's actual code-section hash, not a second implementation of normalization.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import contrib
from compare import check_relocation_layout, code_section_sha256, find_function
from pecoff import CoffObject, Reject
from source_digest import include_closure, tu_digest

SELF_TEST_RVAS = (contrib.SELF_TEST_RVA, 0x405a50, 0x1f3560)


def probe(root, bindir):
    """Measure all four pinned binaries; a version banner alone is insufficient."""
    files = []
    for name, expected in contrib.pinned_hashes(root).items():
        path = bindir / name
        actual = contrib.sha256_file(path) if path.is_file() else None
        files.append(dict(name=name, size=path.stat().st_size if path.is_file() else None,
                          sha256=actual, expected_sha256=expected, equal=actual == expected))
    env = {k: v for k, v in os.environ.items() if k.upper() not in ('CL', '_CL_')}
    result = subprocess.run([str(bindir / 'cl.exe')], env=env, capture_output=True,
                            text=True, errors='replace', timeout=30)
    banner = result.stdout + result.stderr
    version = re.search(r'Version (19\.\d+\.\d+)(?:\.\d+)? for (x64|x86)', banner)
    version_ok = bool(version and version.group(1) == '19.16.27054' and version.group(2) == 'x64')
    return dict(schema=1, kind='toolchain-probe',
                version=version.group(0) if version else 'unrecognized',
                toolset='MATCH' if version_ok and files and all(f['equal'] for f in files) else 'MISMATCH',
                files=files)


def reference(root, rva):
    """Only an accepted, currently bound, single-code-section public record is a reference."""
    inventory = json.loads((root / 'data/progress.json').read_text())
    fn = next(f for f in inventory['functions'] if f['rva'] == rva)
    if fn['status'] != 'matched':
        raise ValueError('self-test reference is no longer matched')
    record = json.loads((root / fn['report']).read_text())
    source = record['source']
    closure = include_closure(root, source['compiled'])
    if source['digest'] != tu_digest(root, closure) or sorted(source['translation_unit']) != sorted(closure):
        raise ValueError('self-test reference source is stale')
    reports = [run['report'] for run in record['runs']]
    if not reports or any(r['result'] != 'pass' or r['candidate']['code_sections'] != 1
                          or r['function']['rva'] != rva or r['function']['size'] != fn['size']
                          for r in reports):
        raise ValueError('self-test reference is not a passing single-section record')
    hashes = {r['candidate']['code_section_sha256'] for r in reports}
    symbols = {r['function']['symbol'] for r in reports}
    if len(hashes) != 1 or len(symbols) != 1:
        raise ValueError('self-test reference runs disagree')
    if record['recipe']['sha256'] != contrib.sha256_file(root / record['recipe']['path']):
        raise ValueError('self-test reference recipe is stale')
    return dict(rva=rva, size=fn['size'], unit=source['compiled'], symbol=symbols.pop(),
                recipe=record['recipe']['path'], expected_sha256=hashes.pop())


def candidate_hash(blob, ref):
    obj = CoffObject(blob)
    _, section = find_function(obj, ref['symbol'])
    if len(section.data) != ref['size']:
        raise ValueError('candidate function size differs from public reference')
    check_relocation_layout(section, ref['size'], 'self-test')
    return code_section_sha256(obj, [section])


def self_test(root, bindir, work):
    measured = probe(root, bindir)
    ctx = contrib.Ctx(repo=root, platform='win32', interactive=False)
    tool = dict(status='ok', flavour='native', bin=str(bindir), root=str(bindir.parents[6]))
    rows = []
    for rva in SELF_TEST_RVAS:
        ref = reference(root, rva)
        recipe = json.loads((root / ref['recipe']).read_text())
        _, includes = contrib.sdk_include_dirs(ctx, tool['root'], recipe['sdk'])
        if not includes or includes[0].parent.name != recipe['sdk']:
            raise ValueError('pinned SDK headers are not installed')
        hashes = []
        # Separate clean output directories also exercise timestamp/path independence.
        for attempt in range(2):
            built = contrib.compile_unit(ctx, root, ref['unit'], ref['recipe'],
                                         work / f'{rva:x}' / str(attempt), tool)
            hashes.append(candidate_hash(built['object'].read_bytes(), ref))
        rows.append(dict(rva=hex(rva), unit=ref['unit'], size=ref['size'],
                         expected_sha256=ref['expected_sha256'], sha256=hashes,
                         equal=all(h == ref['expected_sha256'] for h in hashes)))
    return dict(schema=1, kind='public-unit-self-test', toolset=measured['toolset'],
                hash_method='code-section-sha256-v1', functions=rows,
                public_unit_hashes_equal=all(row['equal'] for row in rows),
                acceptance='not-evaluated')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('probe', 'self-test'))
    parser.add_argument('--bin', type=Path, required=True, help='MSVC bin/Hostx64/x64 directory')
    parser.add_argument('--out', type=Path, required=True, help='scratch JSON report; never upload objects or logs')
    args = parser.parse_args(argv)
    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        report = (probe(ROOT, args.bin) if args.command == 'probe' else
                  self_test(ROOT, args.bin, args.out.parent / 'objects'))
    except (ValueError, OSError, StopIteration, KeyError, Reject, contrib.Stop, subprocess.TimeoutExpired) as exc:
        # Compiler diagnostics and local paths stay in scratch, never in Actions logs/artifacts.
        report = dict(schema=1, kind=args.command, error=type(exc).__name__,
                      toolset='ERROR', acceptance='not-evaluated')
        args.out.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
        return 1
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if args.command == 'probe' and os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f'toolset={report["toolset"]}\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write('```json\n' + json.dumps(report, indent=2) + '\n```\n')
    return int(args.command == 'self-test' and
               (report['toolset'] != 'MATCH' or not report['public_unit_hashes_equal']))


if __name__ == '__main__':
    sys.exit(main())
