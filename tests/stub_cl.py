"""Stand-in for cl.exe in tests of tools/contrib.py: no compiler is run.

Called as `python3 stub_cl.py <flags...> /showIncludes /Fo<object> <compiled file>` from the
repository root. It prints a `/showIncludes` note for every repository file of the compiled file's
include closure (as cl does), then writes the object named by SR_STUB_OBJECT, or a synthetic one
from tests/synthetic_pecoff.py, to the /Fo path. SR_STUB_FAIL=1 prints an error and exits 2.
"""
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE))
from source_digest import include_closure  # noqa: E402


def main(argv):
    out = next(a[3:] for a in argv if a.startswith('/Fo'))
    compiled = argv[-1]
    if os.environ.get('SR_STUB_FAIL'):
        print(f'{compiled}(3): error C2143: syntax error: missing \';\' before \'}}\'')
        return 2
    root = Path.cwd()
    for rel in include_closure(root, compiled):
        if rel != compiled:
            print(f'Note: including file: {root / rel}')
    source = os.environ.get('SR_STUB_OBJECT')
    if source:
        shutil.copyfile(source, out)
    else:
        import synthetic_pecoff
        Path(out).write_bytes(synthetic_pecoff.coff_object())
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
