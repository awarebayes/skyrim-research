"""Bind one compiled translation unit to a verify_function task description and build record.

Run from the repository root (or from a copy that keeps the repository layout) after compiling:

    python3 -I tools/verifier/tu_task.py --function-id <inventory id> --symbol <mangled name> \
        --compiled reconstruction/<area>/<Class>.cpp --unit <every file of the unit> \
        --recipe reconstruction/recipes/<recipe>.json --symbols <symbol map> \
        --object <candidate.obj> --out <work dir>

Function identity (build id, RVA, size) is read from data/progress.json and the image hash from
builds/target.json, so a task cannot drift from the inventory it will be checked against. The
source revision is the translation-unit digest of tools/source_digest.py, the same value
tools/check.py recomputes from integrated source. --rva/--size override the inventory only for
negative tests; a task built that way can never satisfy the gate for the inventory entry.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_digest import tu_digest  # noqa: E402


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--function-id', required=True)
    p.add_argument('--symbol', required=True)
    p.add_argument('--compiled', required=True, help='Repository-relative path of the compiled .cpp')
    p.add_argument('--unit', nargs='+', required=True, help='Every repository file of the translation unit')
    p.add_argument('--recipe', required=True)
    p.add_argument('--symbols', required=True, type=Path)
    p.add_argument('--object', required=True, type=Path)
    p.add_argument('--repo', default='.', type=Path, help='Repository root holding the source and metadata')
    p.add_argument('--task-id', default=None, help='Default: the function id')
    p.add_argument('--rva', type=lambda v: int(v, 0), default=None)
    p.add_argument('--size', type=int, default=None)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()

    repo = a.repo.resolve()
    if a.compiled not in a.unit:
        raise SystemExit('--compiled must be one of --unit')
    target = json.loads((repo / 'builds/target.json').read_text())
    progress = json.loads((repo / 'data/progress.json').read_text())
    fns = [f for f in progress['functions'] if f['id'] == a.function_id]
    if len(fns) != 1:
        raise SystemExit(f'no single inventory entry {a.function_id!r}')
    fn = fns[0]
    revision = tu_digest(repo, a.unit)
    recipe = repo / a.recipe
    task = {'task_id': a.task_id or a.function_id, 'build_id': fn['build_id'],
            'target_image_sha256': target['image_sha256'],
            'rva': fn['rva'] if a.rva is None else a.rva, 'size': fn['size'] if a.size is None else a.size,
            'symbol': a.symbol, 'source_revision': revision, 'source_path': a.compiled,
            'recipe_sha256': sha256(recipe)}
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    spec = {'verify_task_schema': 1, 'task': task,
            'recipe': os.path.relpath(recipe, out),
            'symbols': os.path.relpath(a.symbols.resolve(), out),
            'manifest': os.path.relpath(repo / 'builds/target.json', out)}
    record = {'build_record_schema': 1, 'source_revision': revision, 'source_path': a.compiled,
              'recipe_sha256': task['recipe_sha256'], 'object_sha256': sha256(a.object)}
    (out / 'task-file.json').write_text(json.dumps(spec, indent=2) + '\n')
    (out / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    print(out / 'task-file.json')


if __name__ == '__main__':
    main()
