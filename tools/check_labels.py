"""Check `Labels: v2` name-origin labels in reconstruction units against pinned community checkouts.

Runs locally only (Drafters, and `tools/verifier/attempt` after each comparison): the community
checkouts are private clones under `.local/`, so CI does not run it. It reports, it never edits:

- a name labelled COMMUNITY(<owner>/<repo>@<rev>, ...) must exist in that checkout: an enumerator
  in the enum of that name, a member or method within the named class (or one of its bases), or,
  for a name with no scope, a declared identifier, class, enum or namespace anywhere. A class name
  also counts when it appears only in the checkout's RTTI/VTABLE offset lists
  (`RTTI_<Scope>__<Name>`), which is where NG keeps classes it does not declare. A checkout with
  a name list at its root (meh321's `skyrimae.rename`, `<id> <Scope::Name>_*` per line) declares
  each listed name in its scope;
- every enum the unit defines whose name or enumerators carry a COMMUNITY label: each enumerator
  must be spelled as in the community enum of that name, and a value the unit assigns must equal
  the community value;
- a name labelled GUESS (without COMMUNITY) that has a class context and exists in a checkout under
  that class (or a base) is reported with a suggestion to use the community label;
- a name labelled SIBLING(<owner>/<repo>@<rev>, ...) must exist in that sibling decompilation's
  clone ("sibling_checkouts" in the config, default `.local/sources/fnv_decomp`): in its headers
  under `include/`, or as a compiled function of that class in its `build/units.json`; a GUESS
  name the sibling has in the same class is reported with a suggestion to use SIBLING;
- every `Sibling source: <repo>@<rev> <path>[:<line>]` header line names a file (and a line within
  it) that exists in the clone;
- the checkout must be at the labelled revision (`git rev-parse HEAD` starts with it);
- a .cpp's `Evidence:` files must exist, be tracked, and together name the unit: the class whose
  members it defines, a `Task:` id from its header, or every `RVA 0x...` it lists.

The parsing is lexical (comments and strings stripped, braces matched, identifiers followed by a
declarator punctuator taken as declared), so the findings are warnings for a person to read, not
proof: a name can exist in a class for another reason, and macro-built members are seen only as
far as their tokens appear in the class body.

    python3 tools/check_labels.py [--checkout owner/repo=PATH ...] [files...]
    # default files: every reconstruction/**/*.h and *.cpp with "Labels: v2"
    # default checkouts: .local/verifier/config.json "community_checkouts", else .local/sources/
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_reconstruction import LABEL_LINE, LABELS_VERSION, SIBLING_HEADER, SIBLING_SOURCES  # noqa: E402
from build_fnv_index import split_symbol  # noqa: E402

DEFAULT_CHECKOUTS = {
    'CharmedBaryon/CommonLibSSE-NG': '.local/sources/CommonLibSSE-NG',
    'powerof3/CommonLibSSE': '.local/sources/CommonLibSSE-po3',
    'meh321/AddressLibraryDatabase': '.local/sources/AddressLibraryDatabase',
}
# Sibling decompilations (other games of the engine family) usable by maintainer decision,
# docs/authorizations.md. Only their headers and build list are indexed: their source trees are
# large and every name a unit can cite is in one of the two.
DEFAULT_SIBLINGS = {'momusdigital/fnv_decomp': '.local/sources/fnv_decomp'}
SIBLING_DIRS = ('include',)
# Name lists at a checkout's root, read as declarations (meh321's has no headers).
NAME_LISTS = ('skyrimae.rename',)
UNITS_LIST = 'build/units.json'
COMMUNITY = re.compile(r'COMMUNITY\(([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{7,40}), [^)]*\)')
SIBLING = re.compile(r'SIBLING\(([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{7,40}), [^)]*\)')
NAME = re.compile(r'~?[A-Za-z_]\w*(?:::~?[A-Za-z_]\w*)*')
IDENT = re.compile(r'[A-Za-z_]\w*')
COMMENTS = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'', re.S)
# The text between a scope's name and its `{` (base clause) may hold a class-key only inside a
# template argument list: in `template <..., template <...> class Allocator> class Table {` the
# template-template parameter `class Allocator` would otherwise take the body of `Table` as its own,
# while `struct A : public B<struct C> {` is a base clause of A (base_clause_ok).
SCOPE = re.compile(r'\b(class|struct|union|namespace|enum(?:\s+class|\s+struct)?)\s+'
                   r'(?:alignas\s*\([^)]*\)\s*|__declspec\s*\((?:[^()]|\([^()]*\))*\)\s*|\[\[[^\]]*\]\]\s*)*([A-Za-z_]\w*)\b'
                   r'([^;{}()]*)\{')
BASE = re.compile(r'\b(?:public|protected|private)\s+(?:virtual\s+)?((?:\w+::)*\w+)')
# An identifier followed by one of these is being declared (member, method, parameter, enumerator).
DECLARED = re.compile(r'(?<![\w:.>~])([A-Za-z_]\w*)\s*(?=[;,\[{(=)}]|:(?!:))')
ENUMERATOR = re.compile(r'([A-Za-z_]\w*)\s*(?:=\s*([^,]+))?')
RVA = re.compile(r'\bRVA (0x[0-9a-fA-F]+),? \d+ bytes')
EVIDENCE = re.compile(r'(?:findings|reports)/[\w./-]+\.(?:md|json)')
SOURCE_SUFFIXES = ('.h', '.hpp', '.inl', '.cpp')


def base_clause_ok(clause):
    """No class-key outside angle brackets and no `>` closing a bracket the clause did not open."""
    depth = 0
    for token in re.findall(r'[<>]|\b(?:class|struct|union)\b', clause):
        if token == '<':
            depth += 1
        elif token == '>':
            depth -= 1
            if depth < 0:
                return False
        elif depth == 0:
            return False
    return True


def scope_matches(text):
    """SCOPE matches whose base clause is one (base_clause_ok); after a rejected match the search
    resumes just past its start, so the class it overran is still found."""
    pos = 0
    while True:
        m = SCOPE.search(text, pos)
        if m is None:
            return
        if base_clause_ok(m.group(3)):
            yield m
            pos = m.end()
        else:
            pos = m.start() + 1


def strip(text):
    """Comments and literals blanked and macro continuation backslashes dropped, newlines kept."""
    text = text.replace('\\\r\n', ' \n').replace('\\\n', ' \n')
    return COMMENTS.sub(lambda m: re.sub(r'[^\n]', ' ', m.group(0)), text)


def braces(text):
    """{position of '{': position of its matching '}'} for the whole text."""
    match, stack = {}, []
    for i, c in enumerate(text):
        if c == '{':
            stack.append(i)
        elif c == '}' and stack:
            match[stack.pop()] = i
    return match


def int_value(expr, previous=None):
    expr = expr.strip().replace('static_cast<std::uint32_t>', '')
    expr = re.sub(r'(?<=[0-9a-fA-F])[uUlL]+\b', '', expr)
    if not re.fullmatch(r'[0-9a-fA-FxX\s<>|()+-]+', expr):
        return None
    try:
        return int(eval(expr, {'__builtins__': {}}, {}))  # only digits and shift/or operators reach here
    except Exception:  # noqa: BLE001 - anything unparsable is "unknown", not an error
        return None


def enumerators(body):
    """[(name, value or None)] with implicit values counted on from the last known one."""
    out, last = [], -1
    for item in body.split(','):
        m = ENUMERATOR.fullmatch(item.strip())
        if not m:
            continue
        value = int_value(m.group(2)) if m.group(2) else (None if last is None else last + 1)
        out.append((m.group(1), value))
        last = value
    return out


class Index:
    """Scopes, declared identifiers and enum values of one community checkout."""

    def __init__(self, root, dirs=('include', 'src')):
        self.root = Path(root)
        self.scopes = {}     # simple name -> {'declared': set, 'bases': set}
        self.enums = {}      # enum simple name -> {enumerator: set of values (None when unknown)}
        self.declared = set()
        self.tokens = set()
        self.where = {}      # scope simple name -> [(relative path, first line, last line)]
        self.lines = {}      # relative path -> original lines
        for path in sorted(p for d in dirs for p in (self.root / d).rglob('*')
                           if p.suffix in SOURCE_SUFFIXES and p.is_file()):
            raw = path.read_text(errors='replace')
            rel = path.relative_to(self.root).as_posix()
            self.lines[rel] = raw.splitlines()
            self.add(strip(raw), rel)
        for name in NAME_LISTS:
            if (self.root / name).is_file():
                self.add_name_list(self.root / name)
        if (self.root / UNITS_LIST).is_file():
            self.add_units(self.root / UNITS_LIST)

    def add_units(self, path):
        """A sibling decompilation's build list (fnv_decomp's `build/units.json`): every compiled
        function's decorated name declares its method in its class, so a name the sibling defines
        out of line in its 3,000 source files is found without parsing them."""
        units = json.loads(path.read_text()).get('units', [])
        for unit in units:
            for f in unit.get('functions', []):
                cls, method, _kind = split_symbol(f.get('symbol', ''))
                if not method:
                    continue
                self.declared.add(method)
                self.tokens.add(method)
                if cls:
                    scopes = cls.split('::')
                    self.tokens.update(scopes)
                    entry = self.scopes.setdefault(scopes[-1], {'declared': set(), 'bases': set()})
                    entry['declared'].add(method)

    def add_name_list(self, path):
        """A `<id> <Scope::Name>_*` list (meh321's AddressLibraryDatabase): each qualified name
        declares its last component in its scope, so labels are checked like header names."""
        rel = path.relative_to(self.root).as_posix()
        lines = path.read_text(errors='replace').splitlines()
        self.lines[rel] = lines
        for number, line in enumerate(lines, 1):
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            name = parts[1].strip()
            name = name[:-2] if name.endswith('_*') else name
            if not NAME.fullmatch(name):
                continue
            components = name.split('::')
            ident = components[-1]
            self.tokens.update(components)
            self.declared.add(ident)
            for i, scope in enumerate(components[:-1]):
                entry = self.scopes.setdefault(scope, {'declared': set(), 'bases': set()})
                entry['declared'].add(components[i + 1])
                self.where.setdefault(scope, []).append((rel, number, number))

    def add(self, text, rel=None):
        match = braces(text)
        self.tokens.update(IDENT.findall(text))
        self.declared.update(DECLARED.findall(text))
        for m in scope_matches(text):
            open_at = m.end() - 1
            body = text[open_at + 1:match.get(open_at, open_at)]
            entry = self.scopes.setdefault(m.group(2), {'declared': set(), 'bases': set()})
            entry['declared'].update(DECLARED.findall(body))
            entry['bases'].update(b.split('::')[-1] for b in BASE.findall(m.group(3)))
            if rel is not None:
                self.where.setdefault(m.group(2), []).append(
                    (rel, text.count('\n', 0, m.start()) + 1, text.count('\n', 0, match.get(open_at, open_at)) + 1))
            if m.group(1).startswith('enum'):
                values = self.enums.setdefault(m.group(2), {})
                for name, value in enumerators(body):
                    values.setdefault(name, set()).add(value)

    def locate(self, qualified, scope_hint=None, limit=3):
        """[(path, line, text)]: where the checkout declares `qualified`, searching its scope and
        the scope's bases; for a scope name itself, the line that opens it."""
        parts = qualified.split('::')
        ident, scope = parts[-1], (parts[-2] if len(parts) > 1 else scope_hint)
        if scope is None:
            return [(p, a, self.lines[p][a - 1].strip()) for p, a, _b in self.where.get(ident, [])[:limit]]
        pattern = re.compile(rf'(?<![\w:.>~]){re.escape(ident)}\s*(?=[;,\[{{(=)}}]|:(?!:))')
        found, todo, seen = [], [scope], set()
        while todo and len(found) < limit:
            current = todo.pop(0)
            if current in seen:
                continue
            seen.add(current)
            for path, first, last in self.where.get(current, []):
                for number in range(first, min(last, len(self.lines[path])) + 1):
                    line = self.lines[path][number - 1]
                    if pattern.search(line.split('//')[0]):
                        found.append((path, number, line.strip()))
                        if len(found) >= limit:
                            break
            todo += sorted(self.scopes.get(current, {}).get('bases', ()))
        if not found and ident in self.where:
            found = [(p, a, self.lines[p][a - 1].strip()) for p, a, _b in self.where[ident][:limit]]
        return found

    def in_scope(self, scope, ident, seen=None):
        seen = seen if seen is not None else set()
        if scope in seen or scope not in self.scopes:
            return False
        seen.add(scope)
        entry = self.scopes[scope]
        return ident in entry['declared'] or \
            any(self.in_scope(base, ident, seen) for base in entry['bases'])

    def has(self, qualified, scope_hint=None):
        """'scope', 'rtti', 'global' or None: where `qualified` (A::B or B) is found."""
        parts = qualified.split('::')
        ident = parts[-1]
        scope = parts[-2] if len(parts) > 1 else scope_hint
        if scope is not None:
            if self.in_scope(scope, ident) or ident in self.enums.get(scope, {}):
                return 'scope'
        elif ident in self.scopes or ident in self.declared:
            return 'global'
        rtti = f'RTTI_{"__".join(parts)}'
        if rtti in self.tokens or (scope_hint and f'RTTI_{scope_hint}__{ident}' in self.tokens) \
                or (len(parts) == 1 and any(t.startswith(rtti + '__') for t in self.tokens)):
            return 'rtti'
        return None


def unit_scopes(text):
    """[(start line, end line, kind, name)] of the class/struct/enum/namespace bodies in a unit."""
    clean = strip(text)
    match = braces(clean)
    out = []
    for m in scope_matches(clean):
        open_at = m.end() - 1
        out.append((clean.count('\n', 0, open_at) + 1, clean.count('\n', 0, match.get(open_at, open_at)) + 1,
                    m.group(1).split()[0], m.group(2), clean[open_at + 1:match.get(open_at, open_at)]))
    return out


def enclosing(scopes, line):
    inner = [s for s in scopes if s[0] <= line <= s[1] and s[2] in ('class', 'struct', 'union')]
    return max(inner, key=lambda s: s[0])[3] if inner else None


def contexts(name, scopes, line):
    """Scopes a label name is checked in: none for a qualified name (it carries its scope), else the
    class around the label line, else every unit class or enum that declares the name, else none."""
    if '::' in name:
        return [None]
    around = enclosing(scopes, line)
    if around:
        return [around]
    declaring = sorted({s[3] for s in scopes if s[2] != 'namespace' and name in set(DECLARED.findall(s[4]))})
    return declaring or [None]


def label_lines(text):
    """(line, names, labels) per label line. Parenthesised prose in the names part is dropped, and
    the shorthand `A::x, ::y` names `A::y`."""
    for number, line in enumerate(text.splitlines(), 1):
        m = LABEL_LINE.match(line)
        if not m:
            continue
        names, scope = [], None
        for word in re.split(r'[\s,]+', re.sub(r'\([^)]*\)', ' ', m.group('names'))):
            if word.startswith('::') and scope:
                word = scope + word
            if NAME.fullmatch(word):
                names.append(word)
                scope = word.rsplit('::', 1)[0] if '::' in word else scope
        yield number, names, m.group('labels')


def checkout_head(path):
    out = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


class Checker:
    def __init__(self, checkouts, root=ROOT, siblings=None):
        self.root = Path(root)

        def resolve(path):
            return self.root / path if not Path(path).is_absolute() else Path(path)
        self.checkouts = {repo: resolve(path) for repo, path in checkouts.items()}
        self.siblings = {repo: resolve(path)
                         for repo, path in (DEFAULT_SIBLINGS if siblings is None else siblings).items()}
        self.indexes = {}
        self.reported = set()

    def sibling_index(self, repo):
        path = self.siblings.get(repo)
        if path is None or not path.is_dir():
            return None
        key = ('sibling', repo)
        if key not in self.indexes:
            self.indexes[key] = Index(path, dirs=SIBLING_DIRS)
        return self.indexes[key]

    def index(self, repo, rev, where, findings, sibling=False):
        path = (self.siblings if sibling else self.checkouts).get(repo)
        if path is None or not path.is_dir():
            key = ('missing', repo)
            if key not in self.reported:
                self.reported.add(key)
                kind, config = ('SIBLING', 'sibling') if sibling else ('COMMUNITY', 'community')
                findings.append(f'{where}: no local checkout of {repo}; its {kind} labels were not verified '
                                f'(set .local/verifier/config.json "{config}_checkouts")')
            return None
        head = checkout_head(path)
        if head is None or not head.startswith(rev):
            key = ('rev', repo, rev)
            if key not in self.reported:
                self.reported.add(key)
                findings.append(f'{where}: checkout of {repo} is at {head or "an unknown revision"}, the label pins '
                                f'{rev}; names were checked against the checkout as it is')
        if sibling:
            return self.sibling_index(repo)
        if repo not in self.indexes:
            self.indexes[repo] = Index(path)
        return self.indexes[repo]

    def check_file(self, path):
        rel = path.relative_to(self.root).as_posix() if path.is_relative_to(self.root) else str(path)
        text = path.read_text()
        # Sibling body citations are checked in every unit, labelled v2 or not.
        findings = self.check_sibling_sources(rel, text)
        if not LABELS_VERSION.search(text[:4000]):
            return findings
        scopes = unit_scopes(text)
        community_names = {}   # simple or qualified name -> (repo, index)
        for number, names, labels in label_lines(text):
            where = f'{rel}:{number}'
            pins = COMMUNITY.findall(labels)
            sibling_pins = SIBLING.findall(labels)
            for repo, rev, sibling in [(r, v, False) for r, v in pins] + [(r, v, True) for r, v in sibling_pins]:
                index = self.index(repo, rev, where, findings, sibling)
                if index is None:
                    continue
                kind = 'SIBLING' if sibling else 'COMMUNITY'
                for name in names:
                    if name.startswith('~') or name.split('::')[-1].startswith('~'):
                        continue
                    hints = contexts(name, scopes, number)
                    if not sibling:
                        community_names[name] = (repo, index)
                        community_names.setdefault(name.split('::')[-1], (repo, index))
                    if all(index.has(name, hint) is None for hint in hints):
                        where_in = name.rsplit('::', 1)[0] if '::' in name else ' or '.join(h for h in hints if h)
                        findings.append(f'{where}: {name} is labelled {kind}({repo}) but {repo} at {rev} '
                                        f'declares no such name{" in " + where_in if where_in else ""}')
            if 'GUESS' in labels and not pins and not sibling_pins:
                for name in names:
                    if name.split('::')[-1].startswith('~'):
                        continue
                    for hint in contexts(name, scopes, number):
                        if '::' not in name and hint is None:
                            continue
                        found = None
                        for repo, path in self.checkouts.items():
                            if path.is_dir():
                                index = self.indexes.get(repo) or self.indexes.setdefault(repo, Index(path))
                                if index.has(name, hint) == 'scope':
                                    found = repo
                                    break
                        if found:
                            scope = name.rsplit('::', 1)[0] if '::' in name else hint
                            findings.append(f'{where}: {name} is labelled GUESS but {found} declares it in {scope} '
                                            '(or a base); if it is the same member, label it COMMUNITY')
                            break
                        # A name the sibling decompilation has in the same class was very likely read
                        # there; GUESS would hide that origin.
                        for repo in sorted(self.siblings):
                            index = self.sibling_index(repo)
                            if index is not None and index.has(name, hint) == 'scope':
                                found = repo
                                break
                        if found:
                            scope = name.rsplit('::', 1)[0] if '::' in name else hint
                            findings.append(f'{where}: {name} is labelled GUESS but sibling {found} declares it in '
                                            f'{scope}; if you took it from there, label it SIBLING')
                            break
        findings += self.check_enums(rel, text, scopes, community_names)
        if path.suffix == '.cpp':
            findings += self.check_evidence(rel, text)
        return findings

    def check_sibling_sources(self, rel, text):
        """Each `Sibling source:` header line names a file (and line) that exists in the clone."""
        out = []
        for m in SIBLING_HEADER.finditer(text[:4000]):
            repo, rev, path, line = m.group(1), m.group(2), m.group(3), m.group(4)
            if repo not in SIBLING_SOURCES:
                continue  # the lint refuses it
            root = self.siblings.get(repo)
            if root is None or not root.is_dir():
                if ('missing', repo) not in self.reported:
                    self.reported.add(('missing', repo))
                    out.append(f'{rel}: no local checkout of {repo}; its Sibling source lines were not verified')
                continue
            head = checkout_head(root)
            if head is None or not head.startswith(rev):
                key = ('rev', repo, rev)
                if key not in self.reported:
                    self.reported.add(key)
                    out.append(f'{rel}: checkout of {repo} is at {head or "an unknown revision"}, the unit cites {rev}')
            target = (root / path).resolve()
            # The lint refuses `..`; a symlink in the clone could still lead out, so the resolved
            # path must stay inside the clone before anything is read.
            if '..' in Path(path).parts or not target.is_relative_to(root.resolve()):
                out.append(f'{rel}: Sibling source {path} leads outside the {repo} clone; not read')
                continue
            if not target.is_file():
                out.append(f'{rel}: Sibling source {path} does not exist in {repo}')
            elif line and int(line) > len(target.read_text(errors='replace').splitlines()):
                out.append(f'{rel}: Sibling source {path}:{line} is past the end of the file')
        return out

    def check_enums(self, rel, text, scopes, community_names):
        findings = []
        for start, _end, kind, name, body in scopes:
            if kind != 'enum':
                continue
            members = enumerators(body)
            labelled = name in community_names or any(m in community_names or f'{name}::{m}' in community_names
                                                      for m, _ in members)
            if not labelled:
                continue
            repo, index = community_names.get(name) or next(
                community_names.get(m) or community_names.get(f'{name}::{m}') for m, _ in members
                if m in community_names or f'{name}::{m}' in community_names)
            theirs = index.enums.get(name)
            if theirs is None:
                findings.append(f'{rel}:{start}: enum {name} carries COMMUNITY labels but {repo} has no enum {name}')
                continue
            explicit = {m.group(1) for m in ENUMERATOR.finditer(body) if m.group(2)}
            for member, value in members:
                if member not in theirs:
                    findings.append(f'{rel}:{start}: {name}::{member} is not an enumerator of {repo} {name}')
                elif member in explicit and value is not None and None not in theirs[member] \
                        and value not in theirs[member]:
                    findings.append(f'{rel}:{start}: {name}::{member} = {value} here, but {repo} gives '
                                    f'{", ".join(str(v) for v in sorted(theirs[member]))}')
        return findings

    def check_evidence(self, rel, text):
        """The `Evidence:` files exist, are tracked, and between them name the unit.

        A file names the unit when it mentions every compared RVA, or the class whose members the
        unit defines, or the task id of a `Task:` header line: batch selection findings list
        classes and tasks, not each function's RVA, and a Drafter cannot edit them.
        """
        header = text[:4000]
        line = next((ln for ln in header.splitlines() if 'Evidence:' in ln), None)
        rvas = sorted({r.lower() for r in RVA.findall(header)})
        if line is None or not rvas:
            return []
        files = EVIDENCE.findall(line)
        out = []
        absent = [f for f in files if not (self.root / f).is_file()]
        if absent:
            out.append(f'{rel}: Evidence file {", ".join(absent)} does not exist')
        untracked = [f for f in files if f not in absent and not tracked(self.root, f)]
        if untracked:
            out.append(f'{rel}: Evidence file {", ".join(untracked)} is not tracked by git')
        present = [f for f in files if f not in absent]
        found = ''.join((self.root / f).read_text() for f in present)
        names = unit_names(text)
        if any(re.search(rf'(?<![\w-]){re.escape(n)}(?![\w-])', found) for n in names):
            return out
        low = found.lower()
        missing = [r for r in rvas if not re.search(rf'(?<![0-9a-fx]){r}(?![0-9a-f])', low)]
        if missing:
            out.append(f'{rel}: Evidence ({", ".join(files) or "no file"}) names neither the unit '
                       f'({", ".join(sorted(names)) or "no class or task id"}) nor {", ".join(missing)}')
        return out


TASK_LINE = re.compile(r'^//\s*Task:\s*([A-Za-z0-9][\w.-]*)', re.M)
DEFINITION = re.compile(r'^[^\s/#][^;{}\n]*?\b([A-Za-z_]\w*)::~?[A-Za-z_]\w*\s*\(', re.M)


def unit_names(text):
    """Classes whose members a unit defines (out of line, at file scope) and its `Task:` ids."""
    names = set(TASK_LINE.findall(text[:4000]))
    names |= set(DEFINITION.findall(strip(text)))
    return names


def tracked(root, rel):
    try:
        done = subprocess.run(['git', '-C', str(root), 'ls-files', '--error-unmatch', '--', rel],
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0


def community_excerpts(files, checkouts=None, root=ROOT):
    """For a Reviewer: the community declaration of every COMMUNITY-labelled name in `files`, as
    `name: repo path:line: text` lines (several when the name is declared more than once). SIBLING
    names get the sibling clone's header declaration the same way."""
    checker = Checker(checkouts or configured_checkouts(root), root, configured_siblings(root))
    out, seen = [], set()
    for path in files:
        path = Path(path) if Path(path).is_absolute() else root / path
        text = path.read_text()
        if not LABELS_VERSION.search(text[:4000]):
            continue
        scopes = unit_scopes(text)
        for number, names, labels in label_lines(text):
            pins = [(r, v, False) for r, v in COMMUNITY.findall(labels)] + \
                [(r, v, True) for r, v in SIBLING.findall(labels)]
            for repo, rev, sibling in pins:
                ignored = []
                index = checker.index(repo, rev, path.name, ignored, sibling)
                if index is None:
                    if ('missing', repo) not in seen:
                        seen.add(('missing', repo))
                        out.append(f'(no local checkout of {repo}; excerpts omitted)')
                    continue
                for name in names:
                    for hint in contexts(name, scopes, number):
                        key = (repo, name, hint)
                        if key in seen or name.split('::')[-1].startswith('~'):
                            continue
                        seen.add(key)
                        hits = index.locate(name, hint)
                        label = name if '::' in name or hint is None else f'{hint}::{name}'
                        if not hits:
                            out.append(f'{label}: {repo}: not found')
                        out += [f'{label}: {repo} {p}:{n}: {t[:160]}' for p, n, t in hits]
    return out


def configured_checkouts(root=ROOT):
    try:
        config = json.loads((root / '.local/verifier/config.json').read_text())
    except (OSError, ValueError):
        config = {}
    return config.get('community_checkouts') or DEFAULT_CHECKOUTS


def default_files(root=ROOT):
    return sorted(p for p in (root / 'reconstruction').rglob('*') if p.suffix in ('.h', '.cpp'))


def configured_siblings(root=ROOT):
    try:
        config = json.loads((root / '.local/verifier/config.json').read_text())
    except (OSError, ValueError):
        config = {}
    return config.get('sibling_checkouts') or DEFAULT_SIBLINGS


def check(files, checkouts=None, root=ROOT, siblings=None):
    checker = Checker(checkouts or configured_checkouts(root), root,
                      configured_siblings(root) if siblings is None else siblings)
    findings = []
    for path in files:
        findings += checker.check_file(Path(path) if Path(path).is_absolute() else root / path)
    return findings


def main(argv):
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('files', nargs='*')
    p.add_argument('--checkout', action='append', default=[], metavar='OWNER/REPO=PATH')
    p.add_argument('--sibling', action='append', default=[], metavar='OWNER/REPO=PATH')
    args = p.parse_args(argv)
    checkouts = dict(configured_checkouts())
    checkouts.update(dict(c.split('=', 1) for c in args.checkout))
    siblings = dict(configured_siblings())
    siblings.update(dict(c.split('=', 1) for c in args.sibling))
    findings = check(args.files or default_files(), checkouts, siblings=siblings)
    for f in findings:
        print(f'check_labels: {f}')
    print(f'check_labels: {"PASS" if not findings else "WARN"} ({len(findings)} finding(s))')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
