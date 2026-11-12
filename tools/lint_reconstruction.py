"""Deterministic source rules for files under reconstruction/, run by tools/check.py.

These are the mechanical parts of the Reviewer's checklist (docs/verification.md, acceptance
rule item 2), so a Reviewer pass is not spent on them and a Drafter learns them from the tool:

- layout: `reconstruction/<area>/<Class>.h` and `.cpp` with a lowercase area and a class-named
  file; the .cpp includes its own header by quoted name and the header declares the class;
  recipes are `reconstruction/recipes/*.json`; README.md and the generated INDEX.md are the only
  other files;
- banned constructs, checked on the spliced logical lines of tools/source_digest.py (backslash-
  newline joined first) and on all text alike, comments and literals included: there is no
  lexer to mislead, so a word in prose is refused too (over-refusal is the accepted direction).
  Inline assembly (`__asm__`, `__asm`, `_asm`, `asm`), `__emit`, `__pragma`, `_Pragma`, token
  pasting `##`, a `#define` whose body names `__declspec`, `__pragma`, `_Pragma`, an assembly
  keyword, `__emit` or a code-generation-only `__declspec` argument, `__declspec(...)` with
  `naked`, `code_seg`, `allocate` or `safebuffers` anywhere in its argument list, digit
  separators (`1'000`, refused so that no literal can hide from the byte-list rule), string
  literals of `\\x` escapes, and braced lists of eight or more byte-sized integer or character
  literals; `#pragma` other than `once`, `pack` and `warning` (the rest steer code generation
  only), and any `#pragma` line whose first word is not plainly one of those; universal
  character names (`\\u`, `\\U`) anywhere;
- justified constructs: `__forceinline`, `noinline`, `[[msvc::...]]` attributes and codegen
  intrinsics (`INTRINSICS`) only with a `//` comment of three or more words on the same or
  previous line;
- licence: a file with a `COMMUNITY(..., GPL...)` label (or LGPL, AGPL, any case) names GPL in
  its leading comment, every `COMMUNITY(` (any case) is a well-formed label, and a label for a
  repository in `COMMUNITY_LICENCES` (compared without case) spells it as listed and states its
  licence word; in every file, labelled v2 or not;
- name-origin labels: in a file whose leading comment says `Labels: v2`, every label is on a
  `// <names>: <LABEL> [<LABEL>...][; note]` line, LABEL being `COMMUNITY(<owner>/<repo>@<rev>,
  <licence>)`, `SIBLING(<owner>/<repo>@<rev>, <licence>)` (only a sibling decompilation listed in
  `SIBLING_SOURCES`, at its pin, with its licence word; this citation rule applies in every
  file), `GUESS`, `GUESS(low|medium|high)`, `EXE_RTTI`, `STANDIN` or `OBSERVED`;
- sibling bodies: a `Sibling source: <owner>/<repo>@<rev> <path>[:<line>]` line, required by the
  Reviewer when a unit reuses a body or a substantial part of one, sits in the leading comment and
  cites an allowed sibling at its pin with a path free of `..` components (tools/check_labels.py
  checks the path in the clone);
- header comment fields: the leading comment block names the pinned build id and a `Source
  exposure:` category from PROVENANCE.md; a .cpp also gives `RVA 0x...`, `<n> bytes`,
  `Evidence:` with an existing findings/ or reports/ path, `Drafted by` and `Recipe:` with an
  existing recipe; a .h labels name origin (COMMUNITY, SIBLING, GUESS, EXE_RTTI or OBSERVED);
- skeleton not filled: a `SKELETON_TODO...` word (the stub body and paperwork placeholders that
  tools/skeleton.py writes) is refused in every file, except in a working-tree file git does not
  track yet when the whole tree is checked (`tools/check.py` without `--staged`, which lints a
  Drafter's unfinished files beside finished ones). The per-file command, `--staged`, CI on a
  checkout and the acceptance tool all refuse it, and the stub body is an undeclared name, so an
  unfilled stub can neither compile nor be committed or accepted;
- include style: the include-closure scan of tools/source_digest.py accepts the file, every
  include of a repository file is quoted, and no include sits inside a block comment or a
  conditional block (other than the header guard), because the verifier requires the compiler's
  /showIncludes list to equal the closure and such includes are counted but never opened; every
  include names a plain relative path (no drive letter, backslash, leading `/` or `..`), so no
  source can make the compiler open a host file before the verifier's include check runs.

The byte-data rules (`\\x` strings, byte lists) are heuristics: they catch the obvious ways of
smuggling code or data bytes into source, not every way. The Reviewer remains responsible for
rejecting source whose content is raw bytes in any spelling (docs/verification.md).

    python3 tools/lint_reconstruction.py [files...]   # default: every file under reconstruction/
    python3 tools/lint_reconstruction.py --skeleton-ok [files...]   # a fresh skeleton: all else must pass
"""
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_digest import INCLUDE_ROOTS, STRICT_INCLUDE, logical_lines, quoted_includes  # noqa: E402

EXPOSURE = ('black-box', 'community-headers', 'binary-analysis', 'mixed')
NAME_ORIGINS = ('COMMUNITY', 'SIBLING', 'GUESS', 'EXE_RTTI', 'OBSERVED')
ALLOWED_PRAGMAS = {'once', 'pack', 'warning'}
SOURCE = re.compile(r'reconstruction/([a-z][a-z0-9_]*)/([A-Z][A-Za-z0-9_]*)\.(h|cpp)')
CODEGEN_DECLSPEC = r'naked|code_seg|allocate|safebuffers'
ASM = r'__asm__|__asm|_asm|asm'
# Applied to the whole spliced text with no comment or literal state, so nothing can be hidden
# from them by a lexing disagreement; prose that uses these words is refused as well.
BANNED = (
    (re.compile(rf'(?<![A-Za-z0-9_])(?:{ASM})(?![A-Za-z0-9_])'), 'inline assembly'),
    (re.compile(r'(?<![A-Za-z0-9_])__emit(?![A-Za-z0-9_])'), '__emit'),
    (re.compile(r'(?<![A-Za-z0-9_])(?:__pragma|_Pragma)(?![A-Za-z0-9_])'), 'pragma operator'),
    (re.compile(r'##'), 'token pasting (##)'),
    # Refused as bare words, not only inside a parsed `__declspec(...)`: the keyword can reach its
    # argument list through an identity macro or with a comment before the parenthesis.
    (re.compile(rf'(?<![A-Za-z0-9_])(?:{CODEGEN_DECLSPEC})(?![A-Za-z0-9_])'),
     'codegen-only __declspec word (naked, code_seg, allocate, safebuffers)'),
    # A numeric literal with a separator; `u8'a'` and other prefixed character literals start
    # with a letter and are not matched.
    (re.compile(r"(?<![A-Za-z0-9_.])\.?\d[0-9A-Za-z_.]*'[0-9A-Za-z]"), "digit separator (')"),
    (re.compile(r'"(?:[^"\\\n]|\\.)*(?:\\x[0-9A-Fa-f]{1,2}(?:[^"\\\n]|\\.)*){4,}"'), 'string of \\x byte escapes'),
    # A universal character name can spell any character of an identifier or literal in a way the
    # other rules do not read; nothing in a reconstruction needs one.
    (re.compile(r'\\[uU]'), 'universal character name (\\u or \\U escape)'),
)
# Allowed only with a justification comment on the same or the previous line, because they steer
# code generation without changing what the code means; the Reviewer judges the justification.
INTRINSICS = (r'__builtin_\w+|_mm\d*_\w+|_Interlocked\w+|_BitScan\w+|_bittest\w*|__assume|__noop|__nop'
              r'|_ReturnAddress|_AddressOfReturnAddress|__debugbreak|__fastfail|__(?:read|write)(?:fs|gs)\w+'
              r'|__movs[bdwq]|__stos[bdwq]|_rot[lr]\w*|__rdtsc\w*|__cpuid\w*|__lzcnt\w*|__popcnt\w*'
              r'|_byteswap_\w+|__umulh|__mulh|_u?mul128|__shift(?:left|right)128|_addcarry\w*|_subborrow\w*'
              r'|__faststorefence|_ReadWriteBarrier|_ReadBarrier|_WriteBarrier|__prefetch\w*')
JUSTIFIED = (
    (re.compile(r'(?<![A-Za-z0-9_])__forceinline(?![A-Za-z0-9_])'), '__forceinline'),
    (re.compile(r'(?<![A-Za-z0-9_])noinline(?![A-Za-z0-9_])'), 'noinline'),
    (re.compile(r'\[\[\s*msvc\s*::'), '[[msvc::...]] attribute'),
    (re.compile(rf'(?<![A-Za-z0-9_])(?:{INTRINSICS})(?![A-Za-z0-9_])'), 'codegen intrinsic'),
)
JUSTIFICATION = re.compile(r'//\s*(\S+\s+){2,}\S')
DECLSPEC = re.compile(r'(?<![A-Za-z0-9_])__declspec\s*\(')
# Name-origin label grammar, enforced in files whose leading comment says `Labels: v2`
# (docs/drafter-card.md). Older units keep free-form labels: editing them would change their
# digests and reopen accepted matches.
LABELS_VERSION = re.compile(r'\bLabels:\s*v(\d+)\b')
LABEL = (r'(?:COMMUNITY\([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{7,40}, [A-Za-z0-9.+-]+\)'
         r'|SIBLING\([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{7,40}, [A-Za-z0-9.+-]+\)'
         r'|GUESS(?:\((?:low|medium|high)\))?|EXE_RTTI|STANDIN|OBSERVED)')
# Decompilations of other games of the engine family that the maintainer allowed as a source of
# names, declarations and code (docs/authorizations.md, Notes): repository -> (pinned revision
# prefix, the licence word its labels must carry). A SIBLING label or `Sibling source:` line
# citing anything else is refused, so a new sibling needs a recorded decision and an entry here.
SIBLING_SOURCES = {'momusdigital/fnv_decomp': ('91e1b6e8', 'no-licence')}
SIBLING_LABEL = re.compile(r'SIBLING\(([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{7,40}), ([A-Za-z0-9.+-]+)\)')
# Header line of a unit that reuses a body, or a substantial part of one, from a sibling:
# `Sibling source: <owner>/<repo>@<rev> <path>[:<line>]` (several lines for several bodies).
SIBLING_HEADER = re.compile(r'Sibling source:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{7,40})\s+'
                            r'((?:src|include)/[^\s:]+)(?::(\d+))?')
LABEL_LINE = re.compile(rf'^\s*//\s*(?P<names>\S(?:.*?\S)?)\s*:\s*(?P<labels>{LABEL}(?:\s+{LABEL})*)'
                        r'\s*(?:;\s*(?P<note>.*))?$')
LABEL_WORD = re.compile(r'(?<![A-Za-z0-9_])(?:COMMUNITY|SIBLING|GUESS|EXE_RTTI|STANDIN|OBSERVED)[A-Za-z0-9_]*'
                        r'|(?<![A-Za-z0-9_])(?:EXE[- ]RTTI|STAND[- _]IN)(?![A-Za-z0-9_])')
ORIGIN_LABEL = re.compile(r'COMMUNITY\(|SIBLING\(|GUESS|EXE_RTTI|OBSERVED')
DEFINE = re.compile(r'^[ \t]*#[ \t]*define\b(.*)$', re.M)
DEFINE_BANNED = re.compile(rf'(?<![A-Za-z0-9_])(?:__declspec|__pragma|_Pragma|{ASM}|__emit|{CODEGEN_DECLSPEC})'
                           r'(?![A-Za-z0-9_])')
INT_LITERAL = re.compile(r'(?<![\w.])(0[xX][0-9A-Fa-f]+|\d+)[uUlL]*(?![\w.])')
CHAR_LITERAL = re.compile(r"(?:u8|u|U|L)?'(\\x[0-9A-Fa-f]+|\\[0-7]{1,3}|\\.|[^'\\\n])'")
BRACED = re.compile(r'\{([^{}]*)\}', re.S)
INCLUDE_NAME = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_.+-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.+-]*)*')
# The one parent step allowed: a header of another area, `"../<area>/<Class>.h"` (docs/drafter-card.md),
# which from reconstruction/<area>/ stays inside reconstruction/.
SHARED_HEADER = re.compile(r'\.\./[a-z][a-z0-9_]*/[A-Z][A-Za-z0-9_]*\.h')
PRAGMA_LINE = re.compile(r'^[ \t]*#[ \t]*pragma\b(.*)$', re.M)
# Placeholders of tools/skeleton.py (unit_skeleton.py): the stub body and the header fields the
# Drafter has to fill. Any spelling that starts with the prefix counts, so a new placeholder is
# covered without a lint change.
SKELETON_MARKER = re.compile(r'(?<![A-Za-z0-9_])SKELETON_TODO\w*')
PRAGMA_WORD = re.compile(r'[ \t]+([A-Za-z_]\w*)\b(?![ \t]*[^ \t(\n])|[ \t]+([A-Za-z_]\w*)[ \t]*\(')


def spliced_text(blob, name):
    """The file as tools/source_digest.py sees it: logical lines with continuations joined."""
    return '\n'.join(logical_lines(blob, name))


def line_of(text, pos):
    return text.count('\n', 0, pos) + 1


def declspec_arguments(text):
    """(position, argument text) of every `__declspec(...)`, up to its balanced closing parenthesis."""
    for m in DECLSPEC.finditer(text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {'(': 1, ')': -1}.get(text[i], 0)
            i += 1
        yield m.start(), text[m.end():i - 1]


def literal_value(item):
    lit = INT_LITERAL.fullmatch(item)
    if lit:
        return int(lit.group(1), 0)
    ch = CHAR_LITERAL.fullmatch(item)
    if ch:
        body = ch.group(1)
        if body.startswith('\\x'):
            return int(body[2:], 16)
        if re.fullmatch(r'\\[0-7]{1,3}', body):
            return int(body[1:], 8)
        return 0
    return None


def construct_problems(name, text):
    """Banned-construct findings for one file's spliced text."""
    problems = []
    for pattern, what in BANNED:
        hit = pattern.search(text)
        if hit:
            problems.append(f'{name}:{line_of(text, hit.start())}: {what} is not allowed')
    for pos, args in declspec_arguments(text):
        if re.search(rf'(?<![A-Za-z0-9_])(?:{CODEGEN_DECLSPEC})(?![A-Za-z0-9_])', args):
            problems.append(f'{name}:{line_of(text, pos)}: codegen-only __declspec is not allowed')
    lines = text.split('\n')
    for pattern, what in JUSTIFIED:
        for hit in pattern.finditer(text):
            number = line_of(text, hit.start())
            here, before = lines[number - 1], lines[number - 2].strip() if number > 1 else ''
            if not (JUSTIFICATION.search(here) or (before.startswith('//') and JUSTIFICATION.search(before))):
                problems.append(f'{name}:{number}: {what} needs a justification comment (three or more words '
                                'after //) on the same or the previous line')
    for m in DEFINE.finditer(text):
        if DEFINE_BANNED.search(m.group(1)):
            problems.append(f'{name}:{line_of(text, m.start())}: #define naming __declspec, a pragma operator, '
                            'assembly, __emit or a codegen-only __declspec argument is not allowed')
    for m in BRACED.finditer(text):
        values = [literal_value(x.strip()) for x in m.group(1).split(',') if x.strip()]
        values = [v for v in values if v is not None]
        if len(values) >= 8 and all(v <= 0xFF for v in values):
            problems.append(f'{name}:{line_of(text, m.start())}: braced list of 8+ byte-sized integer or '
                            'character literals (raw bytes?)')
    for m in PRAGMA_LINE.finditer(text):
        word = PRAGMA_WORD.match(m.group(1))
        word = word and (word.group(1) or word.group(2))
        if word not in ALLOWED_PRAGMAS:
            shown = word or m.group(1).strip()[:20]
            problems.append(f'{name}:{line_of(text, m.start())}: #pragma {shown} is not allowed '
                            f'(only {", ".join(sorted(ALLOWED_PRAGMAS))}, spelled plainly)')
    return problems


def sibling_problems(where, repo, rev, licence=None):
    """A SIBLING citation must name an allowed sibling at its pinned revision, with its licence word."""
    allowed = SIBLING_SOURCES.get(repo)
    if allowed is None:
        return [f'{where}: {repo} is not an allowed sibling source (allowed: {", ".join(sorted(SIBLING_SOURCES))}; '
                'a new one needs a maintainer decision in docs/authorizations.md)']
    pin, word = allowed
    out = []
    if not (rev.startswith(pin) or pin.startswith(rev)):
        out.append(f'{where}: {repo} is pinned at {pin}, the citation gives {rev}')
    if licence is not None and licence != word:
        out.append(f'{where}: a {repo} label carries the licence word "{word}" (its LICENSE grants none), not "{licence}"')
    return out


def sibling_header_problems(name, header):
    """`Sibling source:` lines in the leading comment are well formed and cite an allowed sibling;
    one outside the leading comment is refused, since readers and tools look for it there."""
    problems = []
    for line in header.splitlines():
        if 'Sibling source:' not in line:
            continue
        m = SIBLING_HEADER.search(line)
        if not m:
            problems.append(f'{name}: write "Sibling source: <owner>/<repo>@<rev> <src/ or include/ path>[:<line>]"')
            continue
        if '..' in PurePosixPath(m.group(3)).parts:
            # check_labels.py opens this path in the clone; `..` would let it read outside it.
            problems.append(f'{name}: a Sibling source path may not contain ".." components')
        problems += sibling_problems(name, m.group(1), m.group(2))
    return problems


def label_problems(name, text, header, ext):
    """`Labels: v2` grammar: a label line is `// <names>: <LABEL> [<LABEL>...][; note]`, and no
    label word appears anywhere else, so every label is attached to the names it describes."""
    version = LABELS_VERSION.search(header)
    if not version:
        return []
    if version.group(1) != '2':
        return [f'{name}: unknown "Labels: v{version.group(1)}" (only v2 is defined)']
    problems, labelled = [], 0
    for number, line in enumerate(text.split('\n'), 1):
        if not LABEL_WORD.search(line):
            continue
        m = LABEL_LINE.match(line)
        rest = m and (m.group('names') + ' ' + (m.group('note') or ''))
        if not m or LABEL_WORD.search(rest):
            problems.append(f'{name}:{number}: label outside the v2 grammar; write "// <names>: <LABEL> ...[; note]" '
                            'with LABEL one of COMMUNITY(<owner>/<repo>@<rev>, <licence>), '
                            'SIBLING(<owner>/<repo>@<rev>, <licence>), GUESS, '
                            'GUESS(low|medium|high), EXE_RTTI, STANDIN, OBSERVED')
            continue
        if not ORIGIN_LABEL.search(m.group('labels')):
            problems.append(f'{name}:{number}: STANDIN also needs the origin of the name (COMMUNITY(...), SIBLING(...), '
                            'GUESS, EXE_RTTI or OBSERVED)')
        labelled += 1
    if ext == 'h' and not labelled:
        problems.append(f'{name}: a "Labels: v2" header needs at least one "// <names>: <LABEL>" line')
    return problems


GPL_LABEL = re.compile(r'COMMUNITY\([^)]*,\s*(?:A|L)?GPL', re.I)
# The licence word each known community repository's labels carry (docs/drafter-card.md and
# docs/authorizations.md): a label stating another licence for one of these misstates provenance.
# A repository not listed here is not refused by this rule; the Reviewer judges its licence word.
COMMUNITY_LICENCES = {
    'CharmedBaryon/CommonLibSSE-NG': 'MIT',
    'powerof3/CommonLibSSE': 'GPL-3.0',
    'meh321/AddressLibraryDatabase': 'permission',
}
COMMUNITY_LABEL = re.compile(r'COMMUNITY\(([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{7,40}), ([A-Za-z0-9.+-]+)\)')
# Any case: a `community(` written in another case is still read as a label by a person.
COMMUNITY_OPEN = re.compile(r'community\(', re.I)


def licence_problems(name, text, header):
    """A file with a GPL-licensed COMMUNITY label states GPL in its header (docs/authorizations.md);
    the wording of the statement is the Reviewer's to judge, its presence is checked here. Every
    `COMMUNITY(` (any case) is a label of the grammar `COMMUNITY(<owner>/<repo>@<rev>, <licence>)`,
    and a label naming a repository of COMMUNITY_LICENCES (owner and repository compared without
    case) spells it as listed and carries its licence word. All of this applies to every file,
    labelled v2 or not, since a label anywhere is a provenance claim; a malformed label would
    otherwise slip past the table."""
    problems = []
    hit = GPL_LABEL.search(text)
    if hit and not re.search(r'GPL', header, re.I):
        problems.append(f'{name}:{line_of(text, hit.start())}: a GPL-licensed COMMUNITY label needs the file\'s '
                        'leading comment to state the GPL licence')
    known = {repo.casefold(): repo for repo in COMMUNITY_LICENCES}
    for opening in COMMUNITY_OPEN.finditer(text):
        where = f'{name}:{line_of(text, opening.start())}'
        m = COMMUNITY_LABEL.match(text, opening.start())
        if not m:
            problems.append(f'{where}: a COMMUNITY( label is not "COMMUNITY(<owner>/<repo>@<rev>, <licence>)" '
                            '(upper case, lower-case hex revision, one licence word)')
            continue
        repo, _, licence = m.groups()
        listed = known.get(repo.casefold())
        if listed is None:
            continue
        if repo != listed:
            problems.append(f'{where}: write the repository as {listed}, not {repo}')
        if licence != COMMUNITY_LICENCES[listed]:
            problems.append(f'{where}: {listed} is licensed "{COMMUNITY_LICENCES[listed]}"; '
                            f'the label states "{licence}"')
    return problems


def sibling_label_problems(name, text):
    """Every SIBLING(...) label in the file cites an allowed sibling at its pin with its licence
    word, whether or not the file declares `Labels: v2` (the v2 grammar check adds nothing here)."""
    problems = []
    for m in SIBLING_LABEL.finditer(text):
        problems += sibling_problems(f'{name}:{line_of(text, m.start())}', *m.groups())
    if len(re.findall(r'SIBLING\(', text)) != len(SIBLING_LABEL.findall(text)):
        problems.append(f'{name}: a SIBLING( label is not "SIBLING(<owner>/<repo>@<rev>, <licence>)"')
    return problems


def leading_comment(text):
    """The comment block at the top of the file (before the first code line)."""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('//') or s.startswith('/*') or s.startswith('*') or not s:
            lines.append(s)
        else:
            break
    return '\n'.join(lines)


def include_layout_problems(name, text):
    """Includes in block comments or conditional blocks (header guard excepted)."""
    problems, depth, in_block, guard = [], 0, False, None
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        s = line.strip()
        if in_block:
            if STRICT_INCLUDE.fullmatch(line):
                problems.append(f'{name}:{number}: include inside a block comment')
            if '*/' in s:
                in_block = False
            continue
        if s.startswith('/*') and '*/' not in s:
            in_block = True
            continue
        directive = re.match(r'#\s*(\w+)\s*(\w*)', s)
        if directive:
            word, arg = directive.groups()
            if word == 'ifndef' and depth == 0 and guard is None:
                following = lines[number].strip() if number < len(lines) else ''
                if re.fullmatch(rf'#\s*define\s+{re.escape(arg)}\s*', following):
                    guard = number
                    continue
            if word in {'if', 'ifdef', 'ifndef'}:
                depth += 1
            elif word == 'endif':
                if depth == 0 and guard is not None:
                    guard = -1
                else:
                    depth = max(depth - 1, 0)
            elif word == 'include' and depth > 0:
                problems.append(f'{name}:{number}: include inside a conditional block')
    return problems


def skeleton_problems(name, text):
    """One finding per line that still holds a skeleton placeholder."""
    problems = []
    for number, line in enumerate(text.split('\n'), 1):
        hit = SKELETON_MARKER.search(line)
        if hit:
            problems.append(f'{name}:{number}: skeleton not filled: replace {hit.group(0)} '
                            '(a stub body or a header placeholder from tools/skeleton.py)')
    return problems


def lint_file(root, name, target_build, skeleton_ok=False):
    """Findings for one file; `skeleton_ok` skips only the skeleton-placeholder rule."""
    root = Path(root)
    problems = []
    path = PurePosixPath(name)
    if name in ('reconstruction/README.md', 'reconstruction/INDEX.md'):
        return problems
    if len(path.parts) == 3 and path.parts[1] == 'recipes':
        if path.suffix != '.json':
            problems.append(f'{name}: recipes are reconstruction/recipes/<name>.json')
        return problems
    m = SOURCE.fullmatch(name)
    if not m:
        return [f'{name}: sources are reconstruction/<area>/<Class>.h or .cpp (lowercase area, one class per pair)']
    area, cls, ext = m.groups()
    blob = (root / name).read_bytes()
    try:
        text = blob.decode('utf-8')
    except UnicodeDecodeError:
        return [f'{name}: not UTF-8']
    try:
        targets = quoted_includes(blob, name)
    except ValueError as exc:
        problems.append(str(exc))
        targets = []
    problems += include_layout_problems(name, text.replace('\\\n', ''))
    for kind, target in targets:
        # The compiler opens an include before the verifier's /showIncludes check can refuse it, so a
        # name that could reach a host file (drive letter, backslash, absolute or parent path) is
        # refused here, before any compile of contributed source.
        shared = kind == '"' and SHARED_HEADER.fullmatch(target)
        if not shared and (not INCLUDE_NAME.fullmatch(target) or '..' in target.split('/')):
            problems.append(f'{name}: include name {target!r} must be a plain relative path '
                            '(letters, digits, _ . + - and /; no drive, backslash, leading / or ..), '
                            'or "../<area>/<Class>.h" for another area\'s header')
        if kind == '<':
            for base in INCLUDE_ROOTS:
                if (root / base / target).exists():
                    problems.append(f'{name}: repository header <{target}> must be included as "{target}"')
    try:
        spliced = spliced_text(blob, name)
    except ValueError as exc:
        problems.append(str(exc))
        spliced = text
    problems += construct_problems(name, spliced)
    if not skeleton_ok:
        problems += skeleton_problems(name, spliced)
    header = leading_comment(text)
    if target_build and target_build not in header:
        problems.append(f'{name}: header comment must name the build id {target_build}')
    problems += label_problems(name, spliced, header, ext)
    problems += licence_problems(name, spliced, header)
    problems += sibling_label_problems(name, spliced)
    problems += sibling_header_problems(name, header)
    if 'Sibling source:' in spliced and spliced.count('Sibling source:') != header.count('Sibling source:'):
        problems.append(f'{name}: "Sibling source:" lines belong in the leading comment')
    exposure = re.search(r'Source exposure:\s*([a-z-]+)', header)
    if not exposure or exposure.group(1) not in EXPOSURE:
        problems.append(f'{name}: header comment needs "Source exposure: <{"|".join(EXPOSURE)}>"')
    if ext == 'cpp':
        if not re.search(r'\bRVA 0x[0-9a-fA-F]+', header) or not re.search(r'\b\d+ bytes\b', header):
            problems.append(f'{name}: header comment needs "RVA 0x<rva>" and "<n> bytes" for each compared function')
        if 'Drafted by' not in header:
            problems.append(f'{name}: header comment needs "Drafted by <model or person>"')
        evidence = re.findall(r'Evidence:\s*([^\s,;]+)', header)
        if not evidence:
            problems.append(f'{name}: header comment needs "Evidence: <findings/ or reports/ path>"')
        for ref in evidence:
            ref = ref.rstrip('.')
            if PurePosixPath(ref).parts[:1] not in {('findings',), ('reports',)} or not (root / ref).is_file():
                problems.append(f'{name}: evidence {ref} is not an existing findings/ or reports/ file')
        recipe = re.search(r'Recipe:\s*(\S+)', header)
        if not recipe or not recipe.group(1).startswith('reconstruction/recipes/') \
                or not (root / recipe.group(1).rstrip('.,;')).is_file():
            problems.append(f'{name}: header comment needs "Recipe: reconstruction/recipes/<name>.json" (existing)')
        if ('"', f'{cls}.h') not in targets:
            problems.append(f'{name}: must include its own header as #include "{cls}.h"')
        if not (root / f'reconstruction/{area}/{cls}.h').is_file():
            problems.append(f'{name}: header reconstruction/{area}/{cls}.h is missing')
    else:
        if not any(re.search(rf'\b{o}\b', header) for o in NAME_ORIGINS):
            problems.append(f'{name}: header comment must label name origin ({", ".join(NAME_ORIGINS)})')
        if not re.search(rf'\b(?:class|struct)\s+{re.escape(cls)}\b(?!\s*;)', spliced):
            problems.append(f'{name}: header must declare class {cls}')
    return problems


def lint_tree(root=ROOT, names=None, skeleton_ok=()):
    """Findings for `names` (default: every file under reconstruction/); files in `skeleton_ok`
    may still hold skeleton placeholders."""
    root = Path(root)
    skeleton_ok = set(skeleton_ok)
    target = json.loads((root / 'builds/target.json').read_text())
    if names is None:
        base = root / 'reconstruction'
        names = sorted(p.relative_to(root).as_posix() for p in base.rglob('*') if p.is_file()) if base.is_dir() else []
    problems = []
    for name in names:
        problems += lint_file(root, name, target.get('build_id'), name in skeleton_ok)
    return problems


def main(argv):
    skeleton_ok = '--skeleton-ok' in argv
    names = [a for a in argv if a != '--skeleton-ok']
    problems = lint_tree(ROOT, names or None, names if skeleton_ok else ())
    for p in problems:
        print(p)
    print(f'lint_reconstruction: {"FAIL" if problems else "PASS"} ({len(problems)} problem(s))')
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
