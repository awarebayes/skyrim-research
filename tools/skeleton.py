#!/usr/bin/env python3
"""Write starting .h and .cpp files for a unit from its private task directory.

    python3 tools/skeleton.py .local/tasks/<group>/<unit dir>        # one unit
    python3 tools/skeleton.py .local/tasks/<group>                   # every unit of a group without files
    python3 tools/skeleton.py <dir> --drafted-by <model>             # fill the "Drafted by" line now
    python3 tools/skeleton.py <dir> --sheets [--sibling | --no-sibling]  # also write sheets (both variants
                                                                         # unless one is chosen; tools/sheet.py)

The files have every header line and label the lint needs, the class shell and one stub per
compared function (tools/unit_skeleton.py). A stub body is `SKELETON_TODO_BODY;`, which does not
compile, and the lint refuses every `SKELETON_TODO...` word outside an untracked working file, so
an unfilled skeleton can never pass the comparator, be committed or be accepted. Existing files
are never overwritten (exit 1 for that unit). Exit 0 when every requested unit was written.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from unit_skeleton import REPO, SkeletonError, write_sheet_variants, write_skeleton  # noqa: E402


def unit_dirs(path):
    path = Path(path)
    if (path / 'task.json').is_file():
        return [path]
    if (path / 'group.json').is_file():
        group = json.loads((path / 'group.json').read_text())
        return [path / u['dir'] for u in group['units']]
    raise SkeletonError(f'{path} has neither task.json nor group.json')


def resolve(arg):
    path = Path(arg)
    return path if path.is_absolute() or path.exists() else REPO / path


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('task_dir', help='a unit task directory, or a group directory for all its units')
    p.add_argument('--drafted-by', help='model or person who will write the bodies')
    p.add_argument('--sheets', action='store_true', help='also write sheet.md and sheet-<rva>.md files')
    p.add_argument('--sibling', '--sibling-snippet', dest='sibling', action=argparse.BooleanOptionalAction,
                   default=None, help='only the sheet variant with (or without) FNV bodies; default both')
    a = p.parse_args(argv)
    code = 0
    try:
        dirs = unit_dirs(resolve(a.task_dir))
    except (SkeletonError, OSError, ValueError, KeyError) as exc:
        print(f'skeleton: {exc}', file=sys.stderr)
        return 2
    for d in dirs:
        try:
            h, cpp = write_skeleton(d, a.drafted_by)
            print(f'wrote {h} and {cpp}; next: fill each SKELETON_TODO, then '
                  f'tools/verifier/attempt {d.relative_to(REPO) if d.is_relative_to(REPO) else d}')
        except SkeletonError as exc:
            print(f'skeleton: {exc}', file=sys.stderr)
            code = 1
        if a.sheets:
            try:
                written = write_sheet_variants(d, a.sibling)
                print(f'  sheets: {len(written)} files in {d.name}/ (start with sheet.md)')
            except (SkeletonError, OSError) as exc:
                print(f'skeleton: sheets for {d.name}: {exc}', file=sys.stderr)
                code = 1
    return code


if __name__ == '__main__':
    raise SystemExit(main())
