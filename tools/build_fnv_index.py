"""Build the private lookup index of the Fallout: New Vegas decompilation (sibling source).

The maintainer decided that `momusdigital/fnv_decomp` may be read and reused here
(`docs/authorizations.md`, Notes). This script turns a private clone of it into one JSON line per
FNV function so that a pack, a Drafter or a Reviewer finds the sibling function and its source
line without searching the tree:

- `class`, `method`, `symbol` (decorated name), `address`, `size` (FNV 1.4.0.525, 32-bit x86);
- `source`, `line`, `signature` (first line of the definition, or of the declaration in the
  class's header when the body is inline) and `line_how` (`definition`, `declaration` or null);
- `compiler` and `opt` (`/O2`, `/Od`, `/O1` or null) of the unit that builds it;
- `placeholder`: the class or method name is an address-derived or slot-numbered stand-in
  (`FUN_<addr>`, `vfNN`, `<name>_<8 hex digits>`, ...), not a recovered name;
- `fnv_slot`: the virtual slot the FNV headers imply (declaration order through the primary base
  chain), when every header of the chain was found and the name is not overloaded;
- `ours`: joins to our tables (`.local/analysis/functions.jsonl`, `classes.jsonl`): `{"rva", "how"}`
  with how `name` (our function is named `<class>::<method>`) or `slot` (both sides put an own
  override of the class at the same slot index; `same_name` says whether our slot name agrees).

Nothing here is evidence about the Skyrim binary: FNV is another game, an older engine version
and a 32-bit build whose vtable slots and layouts need not match ours. Slot joins in particular
are positional guesses; the name-agreement count printed at the end says how far to trust them.

The output and the clone stay under `.local/`; run from the repository root:

    python3 tools/build_fnv_index.py [--fnv .local/sources/fnv_decomp] [--analysis .local/analysis]
                                     [--out .local/analysis/fnv_index.jsonl]
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FNV_REPO = 'momusdigital/fnv_decomp'
DEFAULT_FNV = ROOT / '.local/sources/fnv_decomp'
DEFAULT_ANALYSIS = ROOT / '.local/analysis'

OPERATORS = {'2': 'operator new', '3': 'operator delete', '4': 'operator=', '8': 'operator==',
             '9': 'operator!=', 'A': 'operator[]', 'C': 'operator->', 'D': 'operator*', 'E': 'operator++',
             'F': 'operator--', 'G': 'operator-', 'H': 'operator+', 'Y': 'operator+=', 'Z': 'operator-=',
             '_U': 'operator new[]', '_V': 'operator delete[]', 'R': 'operator()', 'B': 'operator cast'}
# Address-derived or numbered names the FNV project uses where it recovered none.
PLACEHOLDER = re.compile(r'(?:^|_)(?:FUN|DAT|LAB|PTR|sub|thunk|unk|UNK)_[0-9A-Fa-f]{5,}|^vf[0-9A-Fa-f]{1,3}$'
                         r'|_[0-9a-fA-F]{8}(?:_|$)|^__Dummy|^Unk_?[0-9A-Fa-f]+$|^[A-Za-z]+_[0-9a-f]{6,8}$|[A-Za-z]\d{3,}$')
# `Scope::Name(` at the start of a line: an out-of-line definition (or its first line).
DEFINITION = re.compile(r'^(?![\s/#])[^;]*?\b((?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)::(~?[A-Za-z_]\w*|operator\s*\S+?)\s*\(')
FREE_DEFINITION = re.compile(r'^(?![\s/#])(?!(?:return|if|while|for|switch|else|do|case)\b)[^;=()]*?\b([A-Za-z_]\w*)\s*\([^;]*$')
CLASS_HEAD = re.compile(r'^\s*(?:class|struct)\s+(?:__declspec\([^)]*\)\s*)?([A-Za-z_]\w*)\b([^;]*)$')
PRIMARY_BASE = re.compile(r':\s*(?:public|protected|private)?\s*(?:virtual\s+)?((?:\w+::)*\w+)')
VIRTUAL = re.compile(r'^\s*virtual\s+[^;(]*?(~?[A-Za-z_]\w*)\s*\(')


def opt_level(flags):
    """'/O2', '/Od' or '/O1' from a unit's flag list (the last optimisation switch wins, as in cl)."""
    level = None
    for f in flags if isinstance(flags, list) else str(flags).split():
        if f in ('/O2', '/Od', '/O1', '/Ox'):
            level = f
    return level


def split_symbol(sym):
    """(class or None, method, kind) from an MSVC decorated name; kind is ctor, dtor,
    deleting-dtor, operator, method or free. Template scopes are not decoded (class None)."""
    m = re.match(r'\?\?(_[GEUV]|[0-9A-Z])((?:[A-Za-z_]\w*@)+)@', sym)
    if m:
        code, scopes = m.group(1), [s for s in m.group(2).split('@') if s]
        cls = '::'.join(reversed(scopes))
        last = scopes[0]
        if code == '0':
            return cls, last, 'ctor'
        if code == '1':
            return cls, '~' + last, 'dtor'
        if code in ('_G', '_E'):
            return cls, '~' + last, 'deleting-dtor'
        if code in OPERATORS:
            return cls, OPERATORS[code], 'operator'
        return None, None, None
    m = re.match(r'\?([A-Za-z_]\w*)@((?:[A-Za-z_]\w*@)*)@', sym)
    if not m:
        return None, None, None
    scopes = [s for s in m.group(2).split('@') if s]
    if not scopes:
        return None, m.group(1), 'free'
    return '::'.join(reversed(scopes)), m.group(1), 'method'


def is_placeholder(cls, method):
    parts = [p for p in (cls or '').split('::') if p] + [(method or '').lstrip('~')]
    return any(PLACEHOLDER.search(p) for p in parts if p)


class Tree:
    """Line lookups in the clone: definitions per file, class declarations in headers."""

    def __init__(self, root):
        self.root = Path(root)
        self._defs = {}

    def lines(self, rel):
        path = self.root / rel
        try:
            return path.read_text(errors='replace').splitlines()
        except OSError:
            return []

    def definitions(self, rel):
        """{(last scope or None, name): (line, text)} of the first definition per name at file scope."""
        if rel not in self._defs:
            out = {}
            for number, line in enumerate(self.lines(rel), 1):
                m = DEFINITION.match(line)
                if m:
                    key = (m.group(1).split('::')[-1], re.sub(r'\s+', '', m.group(2)))
                    out.setdefault(key, (number, line.strip()[:200]))
                    continue
                m = FREE_DEFINITION.match(line)
                if m:
                    out.setdefault((None, m.group(1)), (number, line.strip()[:200]))
            self._defs[rel] = out
        return self._defs[rel]


def header_classes(root):
    """{class: {'header', 'line', 'base', 'virtuals': [name], 'decls': {name: (line, text)}}} from
    include/*.h of the clone (the per-class headers; `_decls` and staging copies are not used)."""
    out = {}
    for path in sorted((Path(root) / 'include').glob('*.h')):
        rel = path.relative_to(root).as_posix()
        current, depth, opened = None, 0, False
        for number, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
            code = line.split('//')[0]
            if current is None:
                m = CLASS_HEAD.match(code)
                if m and m.group(1) == path.stem:
                    base = PRIMARY_BASE.search(m.group(2))
                    current = {'header': rel, 'line': number, 'base': base.group(1).split('::')[-1] if base else None,
                               'virtuals': [], 'decls': {}}
                    depth, opened = 0, False
                else:
                    continue
            depth += code.count('{') - code.count('}')
            opened = opened or '{' in code
            if depth == 1:
                v = VIRTUAL.match(code)
                if v:
                    current['virtuals'].append(v.group(1))
                d = re.search(r'(~?[A-Za-z_]\w*)\s*\(', code)
                if d and d.group(1) not in current['decls']:
                    current['decls'][d.group(1)] = (number, line.strip()[:200])
            if opened and depth <= 0:
                out[path.stem] = current
                current = None
                break
    return out


def fnv_slots(cls, headers, memo=None, stack=()):
    """[method name or None per slot] for `cls` from header declaration order, or None when a
    header of the primary chain is missing. A name declared twice in the chain (overloads, whose
    MSVC slot order is not declaration order) is None at each of its slots."""
    memo = {} if memo is None else memo
    if cls in memo:
        return memo[cls]
    h = headers.get(cls)
    if h is None or cls in stack:
        return None
    slots = []
    if h['base']:
        base = fnv_slots(h['base'], headers, memo, stack + (cls,))
        if base is None:
            memo[cls] = None
            return None
        slots = list(base)
    counts = Counter(h['virtuals'])
    for name in h['virtuals']:
        if name.startswith('~'):
            at = next((i for i, n in enumerate(slots) if n and n.startswith('~')), None)
            if at is not None:
                slots[at] = name
                continue
        if counts[name] > 1:
            slots.append(None)
            continue
        if name in slots:
            slots[slots.index(name)] = name
        else:
            slots.append(name)
    memo[cls] = slots
    return slots


def load_ours(analysis):
    """(functions by rva, classes by name) from our tables, or ({}, {}) when they are absent."""
    fns, classes = {}, {}
    analysis = Path(analysis)
    if (analysis / 'functions.jsonl').is_file():
        with open(analysis / 'functions.jsonl') as fh:
            for line in fh:
                r = json.loads(line)
                fns[r['rva']] = r
    if (analysis / 'classes.jsonl').is_file():
        with open(analysis / 'classes.jsonl') as fh:
            for line in fh:
                c = json.loads(line)
                classes[c['class']] = c
    return fns, classes


def our_name_keys(row):
    """{(class, method)} of a function row's names that are neither placeholders nor contradicted
    by the image's vftables."""
    keys = set()
    for n in row.get('names', []):
        if n.get('how') == 'placeholder' or n.get('agrees_with_vtable') is False:
            continue
        name = n.get('name') or ''
        if '::' in name:
            cls, method = name.rsplit('::', 1)
            keys.add((cls, method))
        elif (row.get('owner') or {}).get('class') and n.get('source', '').endswith('-slot'):
            keys.add((row['owner']['class'], name))
    return keys


def build(fnv_root, analysis=DEFAULT_ANALYSIS):
    """(records, counts). Pure apart from reading the two trees."""
    fnv_root = Path(fnv_root)
    units = json.loads((fnv_root / 'build/units.json').read_text())['units']
    tree = Tree(fnv_root)
    headers = header_classes(fnv_root)
    fns, classes = load_ours(analysis)

    records = []
    for u in units:
        opt = opt_level(u.get('flags', []))
        defs = tree.definitions(u['source'])
        for f in u['functions']:
            cls, method, kind = split_symbol(f['symbol'])
            rec = {'class': cls, 'method': method, 'kind': kind, 'symbol': f['symbol'],
                   'address': f['address'], 'size': f['size'], 'source': u['source'], 'line': None,
                   'signature': None, 'line_how': None, 'compiler': u.get('compiler'), 'opt': opt,
                   'placeholder': cls is None and method is None or is_placeholder(cls, method),
                   'fnv_slot': None, 'ours': []}
            if method:
                hit = defs.get((cls.split('::')[-1] if cls else None, method.replace(' ', '')))
                if hit:
                    rec['line'], rec['signature'], rec['line_how'] = hit[0], hit[1], 'definition'
                elif cls:
                    h = headers.get(cls)
                    d = h and h['decls'].get(method)
                    if d:
                        rec['source'], rec['line'], rec['signature'], rec['line_how'] = h['header'], d[0], d[1], \
                            'declaration'
            records.append(rec)

    by_key = defaultdict(list)
    for rec in records:
        if rec['class'] and rec['method']:
            by_key[(rec['class'], rec['method'])].append(rec)

    # FNV slot numbers, on the records of the class that overrides at that slot.
    slot_memo = {}
    for cls in headers:
        slots = fnv_slots(cls, headers, slot_memo)
        if not slots:
            continue
        for i, name in enumerate(slots):
            if not name or name not in headers[cls]['virtuals']:
                continue
            for rec in by_key.get((cls, name), []):
                if rec['kind'] != 'dtor' or not any(r['kind'] == 'deleting-dtor' for r in by_key[(cls, name)]):
                    rec['fnv_slot'] = i

    counts = Counter()
    for rva, row in fns.items():
        for key in our_name_keys(row):
            for rec in by_key.get(key, []):
                rec['ours'].append({'rva': rva, 'how': 'name'})
    for cls, info in classes.items():
        ours = info.get('slots') or []
        theirs = slot_memo.get(cls) if cls in headers else None
        if not theirs:
            continue
        own_fnv = set(headers[cls]['virtuals'])
        for i, name in enumerate(theirs[:len(ours)]):
            if not name or name not in own_fnv:
                continue
            rva = ours[i]
            row = fns.get(rva) or {}
            if (row.get('owner') or {}).get('class') != cls:
                continue  # our slot holds an inherited function; theirs is an override
            slot_name = ((info.get('slot_names') or {}).get(str(i)) or {}).get('name')
            ours_name = slot_name.split('::')[-1] if slot_name else None
            same = None if ours_name is None else (ours_name == name)
            if not by_key.get((cls, name)):
                continue  # declared in the FNV header but not compiled there
            for rec in by_key[(cls, name)]:
                if rec['kind'] == 'dtor' and any(r['kind'] == 'deleting-dtor' for r in by_key[(cls, name)]):
                    continue
                if not any(o['rva'] == rva and o['how'] == 'slot' for o in rec['ours']):
                    rec['ours'].append({'rva': rva, 'how': 'slot', 'slot': i, 'same_name': same})
            counts['slot pairs (both sides override at the same index)'] += 1
            counts['slot pairs, our slot named'] += same is not None
            counts['slot pairs, names agree'] += same is True

    our_classes = set(classes)
    joined_rvas = defaultdict(set)
    for rec in records:
        for o in rec['ours']:
            joined_rvas[o['how']].add(o['rva'])
    counts.update({
        'fnv functions': len(records),
        'fnv functions with a recovered (non-placeholder) name': sum(not r['placeholder'] for r in records),
        'fnv functions with a source line': sum(r['line'] is not None for r in records),
        'fnv functions in /O2 units': sum(r['opt'] == '/O2' for r in records),
        'fnv functions with a derived slot': sum(r['fnv_slot'] is not None for r in records),
        'fnv classes with compiled members': len({r['class'] for r in records if r['class']}),
        'fnv classes that are also our RTTI classes': len({r['class'] for r in records if r['class'] in our_classes}),
        'fnv functions joined to one of ours by name': sum(any(o['how'] == 'name' for o in r['ours']) for r in records),
        'fnv functions joined to one of ours by slot': sum(any(o['how'] == 'slot' for o in r['ours']) for r in records),
        'our functions joined by name': len(joined_rvas['name']),
        'our functions joined by slot': len(joined_rvas['slot']),
        'our functions joined either way': len(joined_rvas['name'] | joined_rvas['slot']),
        'our functions joined only by slot': len(joined_rvas['slot'] - joined_rvas['name']),
    })
    return records, counts


def revision(root):
    out = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('--fnv', default=str(DEFAULT_FNV))
    p.add_argument('--analysis', default=str(DEFAULT_ANALYSIS))
    p.add_argument('--out', default=None, help='default: <analysis>/fnv_index.jsonl')
    args = p.parse_args(argv)
    fnv = Path(args.fnv)
    if not (fnv / 'build/units.json').is_file():
        print(f'build_fnv_index: no build/units.json under {fnv}; clone {FNV_REPO} there first', file=sys.stderr)
        return 2
    records, counts = build(fnv, args.analysis)
    out = Path(args.out or Path(args.analysis) / 'fnv_index.jsonl')
    out.parent.mkdir(parents=True, exist_ok=True)
    rev = revision(fnv)
    with open(out, 'w') as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + '\n')
    meta = {'repo': FNV_REPO, 'revision': rev, 'records': len(records), 'counts': dict(sorted(counts.items())),
            'note': 'Private. FNV PC 1.4.0.525 (32-bit); not evidence about the Skyrim binary.'}
    out.with_suffix('.meta.json').write_text(json.dumps(meta, indent=1) + '\n')
    print(f'build_fnv_index: {FNV_REPO}@{(rev or "unknown")[:8]} -> {out}')
    for k, v in sorted(counts.items()):
        print(f'  {k}: {v}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
