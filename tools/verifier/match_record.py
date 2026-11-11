"""Assemble a public match record from comparator reports, then validate it like CI does.

    python3 tools/verifier/match_record.py --function-id <id> \
        --unit reconstruction/<area>/<Class>.cpp reconstruction/<area>/<Class>.h \
        --compiled reconstruction/<area>/<Class>.cpp --recipe reconstruction/recipes/<r>.json \
        --symbols reports/<build id>/symbol-map.json \
        --run <compiled-on> <compared-on> <report.json> [--run ...] \
        --reproduction '<command>' --build build.json --out reports/<build id>/<rva>.json

`--build` is the record's `build` block (reports/README.md): the flags each compile host
actually ran, the environment it cleared, its object hash and the repository files the compiler
opened, as the hosts' build records state them. `tools/verifier/confirm` writes it.

Reports are embedded exactly as the comparator wrote them; nothing in them is edited or
summarized. The record is refused unless tools/check.py's match validation accepts it for the
inventory entry as if that entry were `matched`. Writing a record does not change the inventory
and is not acceptance; acceptance follows the acceptance rule in docs/verification.md and is
recorded by tools/accept_function.py after a Reviewer approve.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from check import MATCH_RECORD_SCHEMA, ROOT, TOOLCHAIN_PIN, file_sha256, validate_match  # noqa: E402
from source_digest import DIGEST_METHOD, tu_digest  # noqa: E402


def build(args, root=ROOT):
    runs = []
    for compiled_on, compared_on, report in args.run:
        runs.append({'compiled_on': compiled_on, 'compared_on': compared_on,
                     'report': json.loads(Path(report).read_text())})
    return {
        'match_record_schema': MATCH_RECORD_SCHEMA,
        'function_id': args.function_id,
        'source': {'translation_unit': sorted(args.unit), 'compiled': args.compiled,
                   'digest_method': DIGEST_METHOD, 'digest': tu_digest(root, args.unit)},
        'recipe': {'path': args.recipe, 'sha256': file_sha256(root, args.recipe)},
        'toolchain_pin': {'path': TOOLCHAIN_PIN, 'sha256': file_sha256(root, TOOLCHAIN_PIN)},
        'symbol_map': {'path': args.symbols, 'sha256': file_sha256(root, args.symbols)},
        'reproduction': args.reproduction,
        'build': json.loads(Path(args.build).read_text()),
        'notes': args.note or [],
        'runs': runs,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--function-id', required=True)
    p.add_argument('--unit', nargs='+', required=True)
    p.add_argument('--compiled', required=True)
    p.add_argument('--recipe', required=True)
    p.add_argument('--symbols', required=True, help='Repository path of the symbol map the runs used')
    p.add_argument('--run', nargs=3, action='append', required=True,
                   metavar=('COMPILED_ON', 'COMPARED_ON', 'REPORT'))
    p.add_argument('--reproduction', required=True)
    p.add_argument('--build', required=True, help='JSON file with the build block')
    p.add_argument('--note', action='append')
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    record = build(args)
    progress = json.loads((ROOT / 'data/progress.json').read_text())
    target = json.loads((ROOT / 'builds/target.json').read_text())
    fns = [f for f in progress['functions'] if f['id'] == args.function_id]
    if len(fns) != 1:
        raise SystemExit(f'no single inventory entry {args.function_id!r}')
    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    fn = copy.deepcopy(fns[0])
    fn['report'] = out.relative_to(ROOT).as_posix()
    try:
        validate_match(fn, target)
    except (ValueError, KeyError, TypeError) as exc:
        out.unlink()
        raise SystemExit(f'refused: {exc}')
    print(f'wrote {fn["report"]}: {len(record["runs"])} runs, consistent with the integrated source')


if __name__ == '__main__':
    main()
