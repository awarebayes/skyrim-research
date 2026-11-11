"""Source revision of a reconstructed translation unit, as the comparator task and build record use it.

A translation unit is the compiled .cpp plus every repository header it includes. Its revision is
the SHA-256 of the lines `<file sha256>  <repository-relative path>\n`, sorted by path (the
`sha256sum` line format). Hashing paths as well as contents means a moved or renamed header is a
new revision, and a single file's digest cannot be mistaken for the unit's.

    python3 tools/source_digest.py reconstruction/x/A.cpp reconstruction/x/A.h

Which repository files form the unit is not the caller's choice: `include_closure` derives it from
the compiled file's quoted `#include "..."` directives, transitively, and the gate and the
verifier task both require the listed unit to equal that closure. Angle-bracket includes name
toolchain and SDK headers: they are not repository files and are bound by the pinned toolchain
hash (tools/verifier/pinned.sha256), not by this digest.

The scan fails closed by construction and keeps no lexical state (see the comment above
`quoted_includes` and docs/verification.md, "Match gate"): after strict UTF-8 decoding, one BOM
stripped, newline normalisation and continuation splicing, every logical line is either a strict
include (counted, even inside a comment), harmless, or a refusal. A quoted include resolves, in
order, against the including file's directory, the directories of the files that included it (innermost first, as MSVC
searches), then INCLUDE_ROOTS, and must reach exactly one regular file whose real path stays inside
the repository and outside `.local/` and `.git/`, with no symlink in any path component and with
the exact on-disk spelling of every component (Windows hosts look names up case-insensitively).

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
PRIVATE_DIRS = {'.local', '.git'}
STRICT_INCLUDE = re.compile(r'[ \t]*#[ \t]*include[ \t]*(?:"([^"<>\n]+)"|<([^"<>\n]+)>)[ \t]*')
DIRECTIVE_NAME = re.compile(r'#[ \t\f\v]*([A-Za-z_][A-Za-z0-9_]*)')
ALLOWED_DIRECTIVES = {'define', 'undef', 'if', 'ifdef', 'ifndef', 'elif', 'else', 'endif', 'pragma', 'error', 'line'}
INCLUDE_WORDS = ('include', 'import')
# Refused anywhere in a file, whatever lexical context the text might be in.
FILE_REFUSALS = (
    (re.compile(r'include_alias'), '#pragma include_alias remaps include names'),
    (re.compile(r'__has_include'), '__has_include makes the unit depend on files it does not include'),
    (re.compile(r'_Pragma'), '_Pragma can issue pragmas the line scan cannot see'),
    (re.compile(r'(?<![A-Za-z0-9_])(?:u8|u|U|L)?R"'), 'raw string literal prefix'),
    (re.compile(r'\bimport[ \t\f\v]*["<]'), 'import of a header unit'),
    (re.compile(r'%:'), 'digraph %: (an alternative spelling of #)'),
)
BLANKS = ' \t\f\v'


def _refuse(name, what):
    raise ValueError(f'{name}: {what}; the translation unit cannot be derived')


def logical_lines(blob, name):
    """The file's logical lines: strict UTF-8, one BOM stripped, newlines normalised, continuations spliced."""
    try:
        text = blob.decode('utf-8')
    except UnicodeDecodeError as exc:
        _refuse(name, f'not UTF-8 ({exc.reason} at byte {exc.start})')
    if text.startswith('\ufeff'):
        text = text[1:]
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if '??=' in text or '??/' in text:
        _refuse(name, 'trigraph')
    if re.search(r'\\[ \t\f\v]+\n', text):
        # Compilers disagree on whether this splices lines, so its meaning is not fixed.
        _refuse(name, 'backslash followed by blanks at a line end')
    spliced = text.replace('\\\n', '')
    for pattern, what in FILE_REFUSALS:
        # Checked raw and spliced, so a continuation cannot split the word.
        if pattern.search(text) or pattern.search(spliced):
            _refuse(name, what)
    return spliced.split('\n')


# Why no quoted include that MSVC compiles can escape this scan. The scan keeps no lexical state:
# every logical line is examined whether or not it sits in a comment, string or `#if 0`, so it
# can only over-include or refuse. A directive must begin a logical line with `#`, possibly after
# whitespace or comments, and its name `include` must be spelled out on that same logical line:
# continuations are spliced first, macros cannot produce directives, and the other spellings of
# `#` (trigraph `??=`, digraph `%:`) and of a name (universal character names) are refused.
# Hence any line holding a real quoted include contains both `#` and `include`, and such a line
# is either exactly `#include "path"` (counted) or refused. A line whose first non-blank character
# is `#` and whose directive is not on the fixed allow-list is refused, which removes comment
# tricks between `#` and the name, null directives and unknown directives. Lines that are only
# inside comments or strings may be counted or refused too: that over-includes, never under.
def quoted_includes(blob, name):
    """The quoted include targets of one file, in order; raises on any line it cannot classify."""
    targets = []
    for number, line in enumerate(logical_lines(blob, name), 1):
        where = f'{name}:{number}'
        strict = STRICT_INCLUDE.fullmatch(line)
        if strict is not None:
            if strict.group(1) is not None:
                targets.append(strict.group(1))
            continue
        if '#' in line and any(word in line for word in INCLUDE_WORDS):
            _refuse(where, 'a line with # and include/import is not exactly #include "path" or #include <path> '
                    '(reconstruction sources must not mention #include in comments or strings)')
        if '#' in line and re.search(r'\\[uU]', line):
            _refuse(where, 'universal character name on a line with #')
        stripped = line.lstrip(BLANKS)
        if stripped.startswith('#'):
            directive = DIRECTIVE_NAME.match(stripped)
            if directive is None or directive.group(1) not in ALLOWED_DIRECTIVES:
                _refuse(where, 'directive is not one of ' + ', '.join(sorted(ALLOWED_DIRECTIVES | {'include'})))
    return targets


def _repo_file(root, rel):
    """`rel` normalised to a repository-relative POSIX path if it names an admissible file, else None."""
    norm = os.path.normpath(rel).replace(os.sep, '/')
    if norm in {'.', '..'} or norm.startswith('../') or os.path.isabs(norm) or '\\' in norm:
        return None
    parts = norm.split('/')
    if parts[0] in PRIVATE_DIRS:
        return None
    base = os.path.realpath(root)
    current = base
    for part in parts:
        try:
            entries = os.listdir(current)
        except OSError:
            return None
        # Exact spelling, and no sibling differing only in case that a Windows host could pick.
        if part not in entries or sum(e.casefold() == part.casefold() for e in entries) != 1:
            return None
        current = os.path.join(current, part)
        if os.path.islink(current):
            return None
    real = os.path.realpath(current)
    inside = os.path.relpath(real, base).replace(os.sep, '/')
    if real != current or inside.startswith('../') or inside.split('/')[0] in PRIVATE_DIRS:
        return None
    return norm if os.path.isfile(real) else None


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
        for target in quoted_includes((root / name).read_bytes(), name):
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
