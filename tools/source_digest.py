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

The parser fails closed by construction: it normalises each file the way the compiler's early
translation phases do, then treats every directive it cannot classify as an error rather than
skipping it. Per file: strict UTF-8 (one leading BOM stripped), line endings normalised,
backslash-newline continuations spliced, then comments removed by a state machine that respects
string and character literals. Refused anywhere: non-UTF-8 bytes; a backslash followed only by
blanks at a line end; trigraphs `??=` and `??/`; a digraph `%:` starting a line; raw string
literals; an unterminated block comment; `include_alias` (also via `_Pragma`); `__has_include`.
Refused as a directive: `#import`, `#include_next`, and any `#include` that is not exactly
`#include "path"` or `#include <path>`. A quoted include resolves, in order, against the including
file's directory, the directories of the files that included it (innermost first, as MSVC
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
DIRECTIVE = re.compile(r'#[ \t\f\v]*([A-Za-z_][A-Za-z0-9_]*)')
STRICT_INCLUDE = re.compile(r'#[ \t\f\v]*include[ \t\f\v]*(?:"([^"<>\n]+)"|<([^"<>\n]+)>)[ \t\f\v]*')
RAW_PREFIX = re.compile(r'(?:^|[^A-Za-z0-9_])(?:u8|u|U|L)?R$')
BLANKS = ' \t\f\v'


def _refuse(name, what):
    raise ValueError(f'{name}: {what}; the translation unit cannot be derived')


def _strip_comments(text, name):
    """`text` with comments replaced by a space plus the newlines they held; literals kept intact.

    Keeping a block comment's newlines can only turn more text into line starts, so it can make
    the parser see more directives than the compiler does, never fewer.
    """
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '/' and text.startswith('/*', i):
            end = text.find('*/', i + 2)
            if end < 0:
                _refuse(name, 'unterminated block comment')
            out.append(' ' + '\n' * text.count('\n', i, end))
            i = end + 2
        elif c == '/' and text.startswith('//', i):
            end = text.find('\n', i)
            i = n if end < 0 else end
            out.append(' ')
        elif c in '"\'':
            if c == '"' and RAW_PREFIX.search(''.join(out[-4:])):
                # A raw string may hold quotes and comment markers this scanner cannot delimit.
                _refuse(name, 'raw string literal')
            j = i + 1
            while j < n and text[j] != c and text[j] != '\n':
                j += 2 if text[j] == '\\' else 1
            # An unterminated literal ends at the line end, as the scanner then resumes on code.
            j = min(j + 1, n) if j < n and text[j] == c else min(j, n)
            out.append(text[i:j])
            i = j
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def logical_lines(blob, name):
    """The file's lines after the normalisation described in the module doc."""
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
    # Checked before comment removal, raw and spliced, so neither a comment nor a continuation hides it.
    if 'include_alias' in text or 'include_alias' in spliced:
        _refuse(name, '#pragma include_alias remaps include names')
    return _strip_comments(spliced, name).split('\n')


def quoted_includes(blob, name):
    """The quoted include targets of one file, in order; raises on anything it cannot classify."""
    targets = []
    for number, line in enumerate(logical_lines(blob, name), 1):
        stripped = line.lstrip(BLANKS)
        if stripped.startswith('%:'):
            _refuse(f'{name}:{number}', 'digraph %: starts a line')
        if '__has_include' in line:
            _refuse(f'{name}:{number}', '__has_include makes the unit depend on files it does not include')
        if not stripped.startswith('#'):
            continue
        directive = DIRECTIVE.match(stripped)
        if directive is None:
            continue
        word = directive.group(1)
        if word in {'import', 'include_next'}:
            _refuse(f'{name}:{number}', f'#{word} is not supported')
        if word.startswith('include') or word.startswith('import'):
            strict = STRICT_INCLUDE.fullmatch(stripped.rstrip(BLANKS))
            if strict is None or word != 'include':
                _refuse(f'{name}:{number}', 'include line is not exactly #include "path" or #include <path>')
            if strict.group(1) is not None:
                targets.append(strict.group(1))
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
