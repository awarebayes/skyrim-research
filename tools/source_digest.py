"""Source revision of a reconstructed translation unit, as the comparator task and build record use it.

A translation unit is the compiled .cpp plus every repository header it includes. Its revision is
the SHA-256 of the lines `<file sha256>  <repository-relative path>\n`, sorted by path (the
`sha256sum` line format). Hashing paths as well as contents means a moved or renamed header is a
new revision, and a single file's digest cannot be mistaken for the unit's.

    python3 tools/source_digest.py reconstruction/x/A.cpp reconstruction/x/A.h
"""
import hashlib
from pathlib import Path, PurePosixPath
import sys

DIGEST_METHOD = 'tu-sha256-v1'


def tu_digest(root, paths):
    lines = []
    for name in sorted(set(paths)):
        rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError(f'translation unit path must be repository-relative: {name}')
        blob = (Path(root) / rel).read_bytes()
        lines.append(f'{hashlib.sha256(blob).hexdigest()}  {rel}\n')
    if not lines:
        raise ValueError('translation unit has no files')
    return hashlib.sha256(''.join(lines).encode()).hexdigest()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    print(tu_digest(Path.cwd(), sys.argv[1:]))
