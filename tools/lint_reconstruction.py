"""Deterministic source rules for files under reconstruction/, run by tools/check.py.

These are the mechanical parts of the Reviewer's checklist (docs/verification.md, acceptance
rule item 2), so a Reviewer pass is not spent on them and a Drafter learns them from the tool:

- layout: `reconstruction/<area>/<Class>.h` and `.cpp` with a lowercase area and a class-named
  file; the .cpp includes its own header by quoted name and the header declares the class;
  recipes are `reconstruction/recipes/*.json`; README.md is the only other file;
- banned constructs: inline assembly (`__asm`, `asm`), `__emit`, `__pragma`, `_Pragma`,
  `__declspec(naked|code_seg|allocate|safebuffers)`, string literals of `\\x` escapes, and braced
  lists of eight or more byte-sized integer literals (raw code or data bytes); `#pragma` other
  than `once`, `pack` and `warning` (the rest steer code generation only);
- header comment fields: the leading comment block names the pinned build id and a `Source
  exposure:` category from PROVENANCE.md; a .cpp also gives `RVA 0x...`, `<n> bytes`,
  `Evidence:` with an existing findings/ or reports/ path, `Drafted by` and `Recipe:` with an
  existing recipe; a .h labels name origin (COMMUNITY, GUESS, EXE_RTTI or OBSERVED);
- include style: the include-closure scan of tools/source_digest.py accepts the file, every
  include of a repository file is quoted, and no include sits inside a block comment or a
  conditional block (other than the header guard), because the verifier requires the compiler's
  /showIncludes list to equal the closure and such includes are counted but never opened.

    python3 tools/lint_reconstruction.py [files...]   # default: every file under reconstruction/
"""
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_digest import INCLUDE_ROOTS, STRICT_INCLUDE, quoted_includes  # noqa: E402

EXPOSURE = ('black-box', 'community-headers', 'binary-analysis', 'mixed')
NAME_ORIGINS = ('COMMUNITY', 'GUESS', 'EXE_RTTI', 'OBSERVED')
ALLOWED_PRAGMAS = {'once', 'pack', 'warning'}
SOURCE = re.compile(r'reconstruction/([a-z][a-z0-9_]*)/([A-Z][A-Za-z0-9_]*)\.(h|cpp)')
BANNED = (
    (re.compile(r'\b(?:__asm|_asm|asm)\b'), 'inline assembly'),
    (re.compile(r'\b__emit\b'), '__emit'),
    (re.compile(r'\b__pragma\b|\b_Pragma\b'), 'pragma operator'),
    (re.compile(r'__declspec\s*\(\s*(?:naked|code_seg|allocate|safebuffers)\b'), 'codegen-only __declspec'),
    (re.compile(r'"(?:[^"\\\n]|\\.)*(?:\\x[0-9A-Fa-f]{1,2}(?:[^"\\\n]|\\.)*){4,}"'), 'string of \\x byte escapes'),
)
INT_LITERAL = re.compile(r'(?<![\w.])(0[xX][0-9A-Fa-f]+|\d+)[uUlL]*(?![\w.])')
BRACED = re.compile(r'\{([^{}]*)\}', re.S)
PRAGMA = re.compile(r'^[ \t]*#[ \t]*pragma[ \t]+([A-Za-z_]\w*)', re.M)


def strip_comments(text):
    """Text with comments blanked (strings kept), so code rules do not fire on prose."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith('//', i):
            j = text.find('\n', i)
            j = n if j < 0 else j
            out.append(' ' * (j - i))
            i = j
        elif text.startswith('/*', i):
            j = text.find('*/', i + 2)
            j = n if j < 0 else j + 2
            out.append(''.join(ch if ch == '\n' else ' ' for ch in text[i:j]))
            i = j
        elif c in '"\'':
            j = i + 1
            while j < n and text[j] != c and text[j] != '\n':
                j += 2 if text[j] == '\\' else 1
            out.append(text[i:j + 1])
            i = j + 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)


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


def byte_lists(code):
    for m in BRACED.finditer(code):
        items = [x.strip() for x in m.group(1).split(',') if x.strip()]
        values = []
        for item in items:
            lit = INT_LITERAL.fullmatch(item)
            if lit:
                values.append(int(lit.group(1), 0))
        if len(values) >= 8 and all(v <= 0xFF for v in values):
            yield code.count('\n', 0, m.start()) + 1


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


def lint_file(root, name, target_build):
    root = Path(root)
    problems = []
    path = PurePosixPath(name)
    if name == 'reconstruction/README.md':
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
    problems += include_layout_problems(name, text)
    for kind, target in targets:
        if kind == '<':
            for base in INCLUDE_ROOTS:
                if (root / base / target).exists():
                    problems.append(f'{name}: repository header <{target}> must be included as "{target}"')
    code = strip_comments(text)
    for pattern, what in BANNED:
        hit = pattern.search(code)
        if hit:
            problems.append(f'{name}:{code.count(chr(10), 0, hit.start()) + 1}: {what} is not allowed')
    for line in byte_lists(code):
        problems.append(f'{name}:{line}: braced list of 8+ byte-sized integer literals (raw bytes?)')
    for pm in PRAGMA.finditer(code):
        if pm.group(1) not in ALLOWED_PRAGMAS:
            problems.append(f'{name}:{code.count(chr(10), 0, pm.start()) + 1}: #pragma {pm.group(1)} is not allowed '
                            f'(only {", ".join(sorted(ALLOWED_PRAGMAS))})')
    header = leading_comment(text)
    if target_build and target_build not in header:
        problems.append(f'{name}: header comment must name the build id {target_build}')
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
        if not re.search(rf'\b(?:class|struct)\s+{re.escape(cls)}\b(?!\s*;)', code):
            problems.append(f'{name}: header must declare class {cls}')
    return problems


def lint_tree(root=ROOT, names=None):
    root = Path(root)
    target = json.loads((root / 'builds/target.json').read_text())
    if names is None:
        base = root / 'reconstruction'
        names = sorted(p.relative_to(root).as_posix() for p in base.rglob('*') if p.is_file()) if base.is_dir() else []
    problems = []
    for name in names:
        problems += lint_file(root, name, target.get('build_id'))
    return problems


def main(argv):
    problems = lint_tree(ROOT, argv or None)
    for p in problems:
        print(p)
    print(f'lint_reconstruction: {"FAIL" if problems else "PASS"} ({len(problems)} problem(s))')
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
