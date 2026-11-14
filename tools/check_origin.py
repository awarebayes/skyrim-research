"""Report reconstruction bodies that resemble a same-named body in a community or sibling source.

Advisory and local only, like tools/check_labels.py: it reads the private pinned clones under
`.local/sources` (CommonLibSSE-NG, the powerof3 fork, the FNV decompilation), which CI does not
have. It never edits anything and never decides provenance; a Reviewer starts the provenance
check from its list (`.claude/agents/reviewer.md`, item 2).

For every function body and inline method body in a unit (out of line `A::f(...) {...}`, inline in
a class body, constructors with initialiser lists, operators), it looks up bodies with the same
class and method name in each clone, normalises both sides and reports pairs whose token
similarity reaches the threshold:

- comments, preprocessor lines and whitespace are dropped and literals are kept as tokens;
- statements whose callee name contains `assert` (assert, SKSE_ASSERT, static_assert) are dropped;
- `this->` is dropped, and locals and parameters are renamed by order of first appearance, so a
  renamed loop variable or `a_stream` versus `stream` does not hide a copy;
- similarity is difflib's ratio over the two token sequences.

A body that is empty or a single `return` of a literal, a (qualified) name or `this` is reported
as `trivial`: a one-statement accessor necessarily coincides with the community declaration and
is not an adaptation. Every other hit is `adapted`, and is shown with whether the unit's leading
comment names the upstream file (for the FNV clone: a `Sibling source:` line with that path).

What it cannot see: a body copied under another method name or into another class, a body split
into helpers or merged from several, free functions whose community counterpart is a member, and
anything the lexical parser misreads (macro-built members, brace initialisers in an initialiser
list, unusual declarators). A clean report is therefore not proof that nothing was adapted.

The index of each clone is cached under `.local/analysis/origin-index/` keyed by the clone's
HEAD and this tool's parser version, so later runs take about a second.

    python3 tools/check_origin.py [--threshold 0.75] [--all] [--json] [files or unit dirs...]
    # default: every unit under reconstruction/ (each .h/.cpp pair is one unit)
"""
import argparse
import difflib
import hashlib
import json
from local_paths import local_dir, local_path
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PARSER_VERSION = 2
DEFAULT_THRESHOLD = 0.75
DEFAULT_SOURCES = {
    'CharmedBaryon/CommonLibSSE-NG': ('.local/sources/CommonLibSSE-NG', 'MIT', ('include', 'src')),
    'powerof3/CommonLibSSE': ('.local/sources/CommonLibSSE-po3', 'GPL-3.0', ('include', 'src')),
    'momusdigital/fnv_decomp': ('.local/sources/fnv_decomp', 'no-licence', ('include', 'src')),
}
SIBLINGS = {'momusdigital/fnv_decomp'}
FORKS = {'powerof3/CommonLibSSE': 'CharmedBaryon/CommonLibSSE-NG'}
SUFFIXES = ('.h', '.hpp', '.inl', '.cpp', '.cxx', '.cc', '.c')

COMMENT_OR_LITERAL = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'', re.S)
PREPROCESSOR = re.compile(r'^[ \t]*#(?:[^\n]*\\\n)*[^\n]*', re.M)
ACCESS = re.compile(r'\b(?:public|private|protected)\s*:(?!:)')
OPERATOR = re.compile(r'\boperator\s*(<<=|>>=|<=>|<<|>>|<=|>=|->\*?|<|>|\(\s*\)|\[\s*\]|[-+*/%^&|~!=,]+|new\b|delete\b)')
NAME = re.compile(r'((?:[A-Za-z_]\w*\s*::\s*)*(?:~\s*[A-Za-z_]\w*|[A-Za-z_]\w*))\s*\(')
NOT_NAMES = {'if', 'for', 'while', 'switch', 'catch', 'return', 'sizeof', 'alignof', 'decltype', 'noexcept',
             'alignas', '__declspec', 'static_assert', 'requires', 'throw', 'new', 'delete', 'typeid',
             'defined', '__attribute__', 'operator', 'template', 'using', 'typedef'}
# What may follow a parameter list before the body: qualifiers, a trailing return type and an
# initialiser list (the init list is whatever follows a single colon).
AFTER_PARAMS = re.compile(r'(?:\s*(?:const|volatile|noexcept(?:\s*\([^()]*\))?|override|final|mutable|&&?|'
                          r'throw\s*\(\s*\)))*\s*(?:->(?:[^:{]|::)+?)?\s*(?::(?!:)(?P<init>[\s\S]*))?')
CLASS_HEAD = re.compile(r'\b(class|struct|union)\s+(?:(?:alignas|__declspec)\s*\((?:[^()]|\([^()]*\))*\)\s*|'
                        r'\[\[[^\]]*\]\]\s*)*([A-Za-z_]\w*)\s*(?:final\s*)?(?::(?!:)[^;]*)?$')
TOKEN = re.compile(r'[A-Za-z_]\w*|0[xX][0-9a-fA-F]+[uUlL]*|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?[fFuUlL]*|"[^"\n]*"|'
                   r"'[^'\n]*'|::|->|&&|\|\||<<=?|>>=?|[<>=!+\-*/%&|^]=|\+\+|--|\S")
IDENT = re.compile(r'[A-Za-z_]\w*$')
NOT_TYPES = {'return', 'else', 'case', 'new', 'delete', 'throw', 'goto', 'co_return', 'co_yield', 'sizeof',
             'using', 'namespace', 'typename', 'operator', 'do', 'default', 'public', 'private', 'protected'}
LITERAL = re.compile(r'(?:0[xX][0-9a-fA-F]+|\d[\w.]*|".*"|\'.*\'|nullptr|true|false)$')


def clean(text):
    """Comments and preprocessor lines blanked, literals kept with braces and quotes neutralised;
    newlines are kept so offsets map to the original line numbers."""
    text = text.replace('\\\r\n', ' \n').replace('\\\n', ' \n')

    def literal(m):
        s = m.group(0)
        if s.startswith('/'):
            return re.sub(r'[^\n]', ' ', s)
        # A literal stays a single token whose text depends on its content, without braces,
        # semicolons or quotes inside that would confuse the brace walk.
        return s[0] + hashlib.sha1(s.encode()).hexdigest()[:len(s) - 2].ljust(len(s) - 2, '_') + s[0]
    text = COMMENT_OR_LITERAL.sub(literal, text)
    return PREPROCESSOR.sub(lambda m: re.sub(r'[^\n]', ' ', m.group(0)), text)


def brace_pairs(text):
    pairs, stack = {}, []
    for m in re.finditer(r'[{}]', text):
        if m.group(0) == '{':
            stack.append(m.start())
        elif stack:
            pairs[stack.pop()] = m.start()
    return pairs


def untemplate(head):
    """The head with operator symbols named and template argument lists removed."""
    head = OPERATOR.sub(lambda m: 'operator_' + re.sub(r'\s', '', m.group(1)).encode().hex(), head)
    previous = None
    while previous != head:
        previous, head = head, re.sub(r'<[^<>;{}]*>', '', head)
    return head


def function_head(head):
    """(qualified name, parameter text, has an unfinished initialiser) when `head` ends a function
    declarator, else None."""
    head = untemplate(ACCESS.sub(' ', head))
    for m in NAME.finditer(head):
        name = re.sub(r'\s', '', m.group(1))
        if name.split('::')[-1].lstrip('~') in NOT_NAMES:
            continue
        depth, i = 0, m.end() - 1
        for i in range(m.end() - 1, len(head)):
            depth += {'(': 1, ')': -1}.get(head[i], 0)
            if depth == 0:
                break
        if depth:
            return None
        rest = AFTER_PARAMS.fullmatch(head[i + 1:])
        if rest is None:
            continue
        init = (rest.group('init') or '').strip()
        # `X() : a_{ 1 }` -- the brace belongs to the initialiser list, not the body.
        unfinished = bool(init) and bool(re.search(r'[\w>]$', init))
        return name, head[m.end():i], unfinished
    return None


def parameters(text):
    out, depth, chunk = [], 0, ''
    for c in text + ',':
        depth += {'(': 1, '<': 1, '[': 1, ')': -1, '>': -1, ']': -1}.get(c, 0)
        if c == ',' and depth <= 0:
            chunk = chunk.split('=')[0]
            names = re.findall(r'[A-Za-z_]\w*', chunk)
            if len(names) >= 2 or (names and re.search(r'[*&]\s*' + names[-1] + r'\s*$', chunk)):
                out.append(names[-1])
            chunk = ''
        else:
            chunk += c
    return out


def functions(text, with_heads=False):
    """[{class, name, line, params, body}] for every function body in a cleaned text. `class` is
    the innermost class around an inline body or the qualifier of an out-of-line name."""
    pairs = brace_pairs(text)
    out = []

    def walk(lo, hi, cls):
        seg = i = lo
        while True:
            m = re.compile(r'[{};]').search(text, i, hi)
            if m is None:
                return
            pos = m.start()
            if m.group(0) != '{':
                seg = i = pos + 1
                continue
            close = pairs.get(pos, hi)
            head = text[seg:pos]
            plain = untemplate(ACCESS.sub(' ', head)).strip()
            if re.search(r'\benum\b', plain):
                pass
            elif re.search(r'\bnamespace\b|\bextern\s*"', plain) and '(' not in plain:
                walk(pos + 1, close, None)
            elif CLASS_HEAD.search(plain):
                walk(pos + 1, close, CLASS_HEAD.search(plain).group(2))
            else:
                found = function_head(head)
                if found and found[2]:
                    i = close + 1  # an initialiser brace: keep the head growing
                    continue
                if found:
                    name, params, _ = found
                    name = re.sub(r'operator_([0-9a-f]+)', lambda o: 'operator' + bytes.fromhex(o.group(1)).decode(), name)
                    parts = name.split('::')
                    owner = parts[-2] if len(parts) > 1 else cls
                    out.append({'class': owner, 'name': parts[-1], 'line': text.count('\n', 0, pos) + 1,
                                'params': parameters(params), 'body': text[pos + 1:close]})
                    if with_heads:
                        out[-1]['head'] = ACCESS.sub(' ', head)
            seg = i = close + 1

    walk(0, len(text), None)
    return out


def drop_asserts(tokens):
    out, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if 'assert' in t.lower() and IDENT.match(t) and i + 1 < len(tokens) and tokens[i + 1] == '(':
            depth, j = 0, i + 1
            for j in range(i + 1, len(tokens)):
                depth += {'(': 1, ')': -1}.get(tokens[j], 0)
                if depth == 0:
                    break
            i = j + 1 + (j + 1 < len(tokens) and tokens[j + 1] == ';')
            continue
        out.append(t)
        i += 1
    return out


def normalise(body, params=()):
    """The body as a token list with asserts and `this->` dropped and locals renamed."""
    tokens = drop_asserts(TOKEN.findall(body))
    tokens = [t for k, t in enumerate(tokens)
              if not (t == 'this' and k + 1 < len(tokens) and tokens[k + 1] == '->')
              and not (t == '->' and k and tokens[k - 1] == 'this')]
    local = list(params)
    for k in range(1, len(tokens) - 1):
        t, prev, nxt = tokens[k], tokens[k - 1], tokens[k + 1]
        if not IDENT.match(t) or t in NOT_TYPES or t in local:
            continue
        typed = IDENT.match(prev) and prev not in NOT_TYPES and nxt in ('=', ';', '{', '(', ',', ')', '[', ':')
        pointer = prev in ('*', '&', '&&', '>') and k >= 2 and (IDENT.match(tokens[k - 2]) or tokens[k - 2] == '>') \
            and tokens[k - 2] not in NOT_TYPES and nxt in ('=', ';', '{', '[', ',', ')', ':')
        if typed or pointer:
            local.append(t)
    rename = {name: f'$L{n}' for n, name in enumerate(dict.fromkeys(local))}
    return [rename.get(t, t) for t in tokens]


def trivial(tokens):
    """Empty, or one `return` of a literal, `this`, or a name or member path (`x`, `A::k`, `a.b`,
    `a->b`); a call, an index, a cast or an operator makes the body non-trivial."""
    if not tokens:
        return True
    if tokens[0] != 'return' or tokens[-1] != ';':
        return False
    inner = tokens[1:-1]
    if len(inner) == 1:
        return bool(LITERAL.match(inner[0]) or IDENT.match(inner[0]) or inner[0].startswith('$L'))
    return len(inner) >= 3 and len(inner) % 2 == 1 and all(
        (IDENT.match(t) or t.startswith('$L')) if n % 2 == 0 else t in ('::', '.', '->')
        for n, t in enumerate(inner))


def similarity(a, b):
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


# ---------------------------------------------------------------- clone index

def head_of(path):
    out = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


class Clone:
    """Function bodies of one pinned clone, indexed by (class, name)."""

    def __init__(self, repo, path, licence, dirs, cache_dir):
        self.repo, self.path, self.licence, self.dirs = repo, Path(path), licence, dirs
        self.head = head_of(self.path)
        self.index = self._load(cache_dir)
        self._texts = {}

    def _load(self, cache_dir):
        key = hashlib.sha256(f'{self.repo} {self.head} {self.dirs} v{PARSER_VERSION}'.encode()).hexdigest()[:16]
        cache = Path(cache_dir) / f'{self.repo.replace("/", "__")}-{key}.json' if cache_dir else None
        if cache is not None and self.head and cache.is_file():
            try:
                return {tuple(k.split(' ', 1)): v for k, v in json.loads(cache.read_text()).items()}
            except (OSError, ValueError):
                pass
        index = {}
        for path in sorted(p for d in self.dirs for p in (self.path / d).rglob('*')
                           if p.suffix.lower() in SUFFIXES and p.is_file()):
            rel = path.relative_to(self.path).as_posix()
            for n, f in enumerate(functions(clean(path.read_text(errors='replace')))):
                index.setdefault((f['class'] or '', f['name']), []).append([rel, n, f['line']])
        if cache is not None and self.head:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({' '.join(k): v for k, v in index.items()}))
        return index

    def bodies(self, cls, name):
        for rel, n, line in self.index.get((cls or '', name), []):
            if rel not in self._texts:
                self._texts[rel] = functions(clean((self.path / rel).read_text(errors='replace')))
            fns = self._texts[rel]
            if n < len(fns) and fns[n]['name'] == name:
                yield rel, line, normalise(fns[n]['body'], fns[n]['params'])


def configured_sources(root=ROOT, env=None):
    config_path = local_dir(root, env) / 'verifier/config.json'
    try:
        config = json.loads(config_path.read_text())
    except (OSError, ValueError):
        config = {}
    sources = dict(DEFAULT_SOURCES)
    for repo, path in (config.get('community_checkouts') or {}).items():
        if repo in sources:
            sources[repo] = (path, *sources[repo][1:])
    for repo, path in (config.get('sibling_checkouts') or {}).items():
        if repo in sources:
            sources[repo] = (path, *sources[repo][1:])
    return sources


def open_clones(root=ROOT, sources=None, cache=True, env=None):
    root = Path(root)
    clones, missing = [], []
    for repo, (path, licence, dirs) in (sources or configured_sources(root, env)).items():
        path = local_path(root, path, env)
        if not path.is_dir():
            missing.append(repo)
            continue
        clones.append(Clone(repo, path, licence, dirs, local_dir(root, env) / 'analysis/origin-index' if cache else None))
    return clones, missing


# ---------------------------------------------------------------- units

def unit_groups(paths, root=ROOT):
    """{unit stem: [files]} with each .h/.cpp pair one unit; directories expand to their units."""
    root = Path(root)
    files = []
    for p in paths:
        p = Path(p) if Path(p).is_absolute() else root / p
        files += sorted(q for q in p.rglob('*') if q.suffix in ('.h', '.cpp')) if p.is_dir() else [p]
    groups = {}
    for f in files:
        rel = f.relative_to(root).as_posix() if f.is_relative_to(root) else str(f)
        groups.setdefault(rel.rsplit('.', 1)[0], []).append(f)
    return groups


def leading_comment(text):
    lines = []
    for line in text.splitlines():
        if line.startswith('//'):
            lines.append(line)
        elif line.strip():
            break
    return '\n'.join(lines)


def declared(header, repo, rel, method):
    """Whether a unit's leading comment names both the method and the upstream file of a hit (for
    the FNV clone, a `Sibling source:` line with that path). Lexical: it does not check that the
    two mentions belong to one sentence."""
    flat = re.sub(r'\s*\n//\s*', ' ', header)
    if not re.search(rf'(?<![\w~]){re.escape(method.lstrip("~"))}(?!\w)', flat):
        return False
    if repo in SIBLINGS:
        return bool(re.search(rf'Sibling source:\s*{re.escape(repo)}@\w+\s+{re.escape(rel)}\b', header))
    base = rel.rsplit('/', 1)[-1]
    return rel in flat or bool(re.search(rf'(?<![\w.]){re.escape(base)}\b', flat))


def check_unit(files, clones, threshold=DEFAULT_THRESHOLD, root=ROOT):
    """[{function, line, file, repo, path, upstream_line, similarity, trivial, declared}], best
    match per (unit function, repo) at or above the threshold."""
    root = Path(root)
    header = '\n'.join(leading_comment(Path(f).read_text()) for f in files)
    hits = []
    for f in files:
        rel = Path(f).relative_to(root).as_posix() if Path(f).is_relative_to(root) else str(f)
        for fn in functions(clean(Path(f).read_text())):
            ours = normalise(fn['body'], fn['params'])
            label = f'{fn["class"]}::{fn["name"]}' if fn['class'] else fn['name']
            for clone in clones:
                best = None
                for path, line, theirs in clone.bodies(fn['class'], fn['name']):
                    score = similarity(ours, theirs)
                    if best is None or score > best[0]:
                        best = (score, path, line, theirs)
                if best is None or best[0] < threshold:
                    continue
                is_trivial = trivial(ours) and trivial(best[3])
                hits.append({'function': label, 'file': rel, 'line': fn['line'], 'repo': clone.repo,
                             'revision': (clone.head or '')[:7], 'licence': clone.licence, 'path': best[1],
                             'upstream_line': best[2], 'similarity': round(best[0], 3), 'trivial': is_trivial,
                             'declared': None if is_trivial else declared(header, clone.repo, best[1], fn['name']),
                             'fork_of': None})
    # The powerof3 fork carries NG's code; a fork hit no closer than NG's for the same body says
    # where else the text is, not a second origin.
    for h in hits:
        if h['repo'] in FORKS:
            parent = next((g for g in hits if g['repo'] == FORKS[h['repo']] and g['function'] == h['function']
                           and g['file'] == h['file'] and g['line'] == h['line']), None)
            if parent is not None and parent['similarity'] >= h['similarity']:
                h['fork_of'] = parent['repo']
    return hits


def describe(hit, no_sibling_names=False):
    if no_sibling_names and hit['repo'] in SIBLINGS:
        return 'a sibling body similarity finding exists (details omitted)'
    kind = 'trivial, same as community' if hit['trivial'] else 'adapted'
    if hit.get('fork_of'):
        kind += f'; same body as {hit["fork_of"]}, which the fork carries'
    elif not hit['trivial']:
        kind += ('; header names it and the upstream file' if hit['declared']
                 else '; header does NOT name it with the upstream file')
    return (f'{hit["function"]} ~ {hit["repo"]}@{hit["revision"]} {hit["path"]}:{hit["upstream_line"]} '
            f'similarity {hit["similarity"]:.2f} ({kind})')


def function_lines(name, hits):
    """One packet line for an inventory function `Class::method` from a unit's hits."""
    own = [h for h in hits if h['function'] == name]
    if not own:
        return f'community/sibling body similarity: none at or above the threshold for {name}'
    def kind(h):
        if h['trivial']:
            return 'trivial'
        if h['fork_of']:
            return f'adapted, same body as {h["fork_of"]}'
        return 'adapted, ' + ('declared in the header' if h['declared'] else 'NOT declared in the header')
    return 'community/sibling body similarity: ' + '; '.join(
        f'{h["repo"]} {h["path"]} {h["similarity"]:.2f} {kind(h)}' for h in own)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('paths', nargs='*', help='unit files or directories (default reconstruction/)')
    p.add_argument('--threshold', type=float, default=DEFAULT_THRESHOLD)
    p.add_argument('--json', action='store_true', help='one JSON object per hit')
    p.add_argument('--no-cache', action='store_true', help='rebuild the clone indexes in memory only')
    args = p.parse_args(argv)
    clones, missing = open_clones(cache=not args.no_cache)
    for repo in missing:
        print(f'check_origin: no local clone of {repo}; its bodies were not compared', file=sys.stderr)
    pins = ', '.join(f'{c.repo}@{(c.head or "?")[:7]}' for c in clones)
    print(f'check_origin: threshold {args.threshold:.2f}; compared with {pins or "nothing"}')
    total = adapted = 0
    for unit, files in sorted(unit_groups(args.paths or ['reconstruction']).items()):
        hits = check_unit(files, clones, args.threshold)
        if not hits:
            continue
        print(f'{unit}:')
        for h in hits:
            total += 1
            adapted += not h['trivial']
            print(json.dumps(h) if args.json else f'  {describe(h)}')
    print(f'check_origin: {total} hit(s), {adapted} non-trivial')
    return 0


if __name__ == '__main__':
    sys.exit(main())
