#!/usr/bin/env python3
"""Print a compact sheet for one function of a unit, one page at a time.

    python3 tools/sheet.py .local/tasks/<group>/<unit dir>                          # index of the unit
    python3 tools/sheet.py .local/tasks/<group>/<unit dir> --function 0x4aa860      # page 1
    python3 tools/sheet.py .local/tasks/<group>/<unit dir> --function 0x4aa860 --page 2
    python3 tools/sheet.py <unit dir> --write [--sibling-snippet]   # sheet*.md files in the task dir

A page is at most unit_skeleton.SHEET_CAP characters (4000), so it fits one tool output; the last
line says which page comes next. A sheet holds private, game-derived material (the listing and the
decompiler output from the pack): read it locally, never paste it into a tracked file.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from unit_skeleton import REPO, SkeletonError, overview, sheet_pages, write_sheets  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('task_dir', help='a unit task directory (with task.json)')
    p.add_argument('--function', help='RVA of the function, e.g. 0x4aa860')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--write', action='store_true', help='write sheet.md and sheet-<rva>[-p<N>].md into the task dir')
    p.add_argument('--sibling-snippet', action='store_true',
                   help='include the FNV body of a same-named method (private clone)')
    a = p.parse_args(argv)
    d = Path(a.task_dir)
    d = d if d.is_absolute() or d.exists() else REPO / d
    try:
        if a.write:
            written = write_sheets(d, a.sibling_snippet)
            print(f'wrote {len(written)} sheet files in {d}; start with sheet.md')
            return 0
        if not a.function:
            print(overview(d), end='')
            return 0
        pages = sheet_pages(d, a.function, a.sibling_snippet)
    except SkeletonError as exc:
        print(f'sheet: {exc}', file=sys.stderr)
        return 2
    if not 1 <= a.page <= len(pages):
        print(f'sheet: page {a.page} does not exist; this function has {len(pages)} page(s)', file=sys.stderr)
        return 2
    print(pages[a.page - 1], end='' if pages[a.page - 1].endswith('\n') else '\n')
    if a.page < len(pages):
        print(f'(page {a.page} of {len(pages)}; next: python3 tools/sheet.py {a.task_dir} '
              f'--function {a.function} --page {a.page + 1})')
    elif len(pages) > 1:
        print(f'(page {a.page} of {len(pages)}, last)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
