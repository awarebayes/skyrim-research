"""Source revision of a reconstructed translation unit, as the comparator task and build record use it.

A translation unit is the compiled .cpp plus every repository header it includes. Its revision is
the SHA-256 of the lines `<file sha256>  <repository-relative path>\n`, sorted by path (the
`sha256sum` line format). Hashing paths as well as contents means a moved or renamed header is a
new revision, and a single file's digest cannot be mistaken for the unit's.

    python3 tools/source_digest.py reconstruction/x/A.cpp reconstruction/x/A.h

Which repository files form the unit is not the caller's choice: `include_closure` derives it from
the compiled file's quoted `#include "..."` directives, transitively, and the gate and the
verifier task both require the listed unit to equal that closure. A quoted include resolves, in
order, against the including file's directory, the directories of the files that included it
(innermost first, as MSVC searches), then INCLUDE_ROOTS. It must resolve to exactly one regular
file inside the repository; an include that resolves nowhere, to more than one file, or outside
the repository, and any `#include`/`#import` that is neither quoted nor angle-bracketed (a
computed include), fails closed. Angle-bracket includes name toolchain and SDK headers: they are
not repository files and are bound by the pinned toolchain hash (tools/verifier/pinned.sha256),
not by this digest.

    python3 tools/source_digest.py --closure reconstruction/x/A.cpp
"""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import sys

DIGEST_METHOD = 'tu-sha256-v1'
# Repository-relative directories a quoted include may also be written against; a source that
# relies on one must be compiled with the matching `/I <root>`.
INCLUDE_ROOTS = ('reconstruction',)
DIRECTIVE = re.compile(r'^[ \t]*#[ \t]*(include|import)\b(.*)$')
QUOTED = re.compile(r'[ \t]*"([^"\n]+)"')
ANGLE = re.compile(r'[ \t]*<([^>\n]+)>')


def _repo_file(root, rel):
    """`rel` normalised to a repository-relative POSIX path if it names a regular file inside root."""
    norm = os.path.normpath(rel).replace(os.sep, '/')
    if norm.startswith('../') or norm == '..' or os.path.isabs(norm):
        return None
    path = Path(root) / norm
    # A symlink could point outside the repository or at a file the digest would hash twice.
    if not path.is_file() or path.is_symlink():
        return None
    return norm


def quoted_includes(text, name):
    """The quoted include targets of one file, in order; raises on a computed include."""
    targets = []
    for number, line in enumerate(text.splitlines(), 1):
        match = DIRECTIVE.match(line)
        if not match:
            continue
        rest = match.group(2)
        quoted = QUOTED.match(rest)
        if quoted:
            targets.append(quoted.group(1))
        elif not ANGLE.match(rest):
            raise ValueError(f'{name}:{number}: #{match.group(1)} is neither "..." nor <...>; '
                             'the translation unit cannot be derived')
    return targets


def include_closure(root, compiled):
    """Every repository file of the translation unit of `compiled`, sorted; see the module doc."""
    root = Path(root)
    start = _repo_file(root, compiled)
    if start is None or start != PurePosixPath(compiled).as_posix():
        raise ValueError(f'compiled file {compiled} is not a repository-relative regular file')
    seen = {start}
    # The search path depends on who included a file, so each distinct includer chain is resolved;
    # a file already open in its own chain is a cycle stopped by its include guard.
    visited = set()
    stack = [(start, ())]
    while stack:
        name, chain = stack.pop()
        dirs = [PurePosixPath(name).parent] + [PurePosixPath(p).parent for p in reversed(chain)]
        key = (name, tuple(dict.fromkeys(dirs)))
        if key in visited:
            continue
        visited.add(key)
        text = (root / name).read_bytes().decode('utf-8', errors='surrogateescape')
        for target in quoted_includes(text, name):
            found = []
            if not PurePosixPath(target).is_absolute():
                for base in dirs + [PurePosixPath(r) for r in INCLUDE_ROOTS]:
                    hit = _repo_file(root, (base / target).as_posix())
                    if hit is not None and hit not in found:
                        found.append(hit)
            if len(found) != 1:
                what = 'cannot be resolved inside the repository' if not found else f'is ambiguous ({", ".join(found)})'
                raise ValueError(f'{name}: #include "{target}" {what}')
            seen.add(found[0])
            if found[0] != name and found[0] not in chain:
                stack.append((found[0], chain + (name,)))
    return sorted(seen)


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
    if sys.argv[1] == '--closure':
        if len(sys.argv) != 3:
            raise SystemExit(__doc__)
        print('\n'.join(include_closure(Path.cwd(), sys.argv[2])))
    else:
        print(tu_digest(Path.cwd(), sys.argv[1:]))
