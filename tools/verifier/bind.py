"""Bind a task's decorated names to target RVAs from a compiled candidate object (local only).

`tools/verifier/attempt` calls this after every compile, so a Drafter never runs a separate bind
step; `python3 tools/ghidra/export_pack.py bind --task <dir>` runs the same code by hand.

Compared functions (`task.json` `functions[].symbol`). The decorated name is whatever the
Drafter's declarations produce, so it is found in the object, in this order:

1. a hint in `<task dir>/bind-hints.json` whose RVA is the function's RVA;
2. the current symbol, if the object still defines it;
3. the one defined function whose qualified name (template arguments, return type and
   parameters dropped) equals the community name;
4. the one defined function whose member name (last component) equals the community name's.

A defined function is an external symbol at offset 0 of its own code section, which is what the
comparator requires anyway. When a previously bound symbol is gone and another is found, that is
reported as "decorated name changed" with both names, and the old map entry is removed (a stale
entry at the same RVA would be an undeclared alias).

References (relocations that leave a compared function). Each needs a map entry giving the RVA
the game encodes; in order:

1. an entry already in `symbols.json`;
2. a hint naming the symbol (decorated, or qualified as above);
3. by position: the target's own relocated field at the same offset, decoded from the local
   image, when that RVA is one of the pack's listed references of this function (so a
   misaligned candidate cannot bind a wrong address: the decoded value must be a known target);
4. the one pack reference whose community name equals the symbol's qualified name, or failing
   that its member name.

Anything left is listed with the file to edit. The comparator still checks every binding: a
wrong RVA fails with relocation-target-mismatch, it cannot pass.

`bind-hints.json` (private, optional), keys are decorated names (`?...`) or qualified names as
the Drafter wrote them (`BSTimer::QGlobalTimeMultiplier`, `GetArmorKind`), values are RVAs:

    {"?GetArmorKind@@YAHPEAVTESObjectARMO@@@Z": "0x27edf0",
     "BSTimer::QGlobalTimeMultiplier": "0x20ccac8"}

A hint whose RVA is a compared function's RVA names that function's decorated or qualified name.
Use hints for targets without a community name, template members and renamed stand-ins; give
only RVAs listed in the function's pack (never guessed ones).
"""
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from pecoff import CoffObject, PeImage, SCN_CNT_CODE, STORAGE_EXTERNAL  # noqa: E402

UNBOUND = 'unbound:'
HINTS = 'bind-hints.json'
# Comparator reasons that mean "nothing was compared because a name is not bound", not a code difference.
BINDING_REASONS = {'function-symbol-missing', 'unresolved-symbol'}
REL32_TAIL = {0x04: 0, 0x05: 1, 0x06: 2, 0x07: 3, 0x08: 4, 0x09: 5}
ADDR32NB = 0x03
UNDNAME = ('llvm-undname', '/opt/homebrew/opt/llvm/bin/llvm-undname', '/usr/local/opt/llvm/bin/llvm-undname')


def parse_rva(value):
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]+|[0-9]+', value):
        return int(value, 0)
    raise ValueError(f'not an RVA: {value!r}')


def find_undname(objdump=None):
    """llvm-undname, preferably next to the configured llvm-objdump."""
    names = []
    if objdump:
        names.append(str(Path(objdump).with_name('llvm-undname')))
    for name in names + [os.environ.get('SR_UNDNAME')] + list(UNDNAME):
        if name and (shutil.which(name) or (os.path.isfile(name) and os.access(name, os.X_OK))):
            return shutil.which(name) or name
    return None


def strip_templates(text):
    out, depth = [], 0
    for ch in text:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth = max(depth - 1, 0)
        elif depth == 0:
            out.append(ch)
    return ''.join(out)


def qualified(demangled):
    """`Scope::member` from a demangled declaration, without template arguments, types or parameters."""
    if not demangled:
        return None
    text = strip_templates(demangled)
    if '(' in text and 'operator' not in text:
        text = text[:text.index('(')]
    tokens = text.replace('*', ' ').replace('&', ' ').split()
    return tokens[-1] if tokens else None


def fallback_qualified(name):
    """Qualified name for plain `?member@Scope@...@@` decorations without a demangler; None otherwise."""
    m = re.match(r'\?([A-Za-z_]\w*)@((?:[A-Za-z_]\w*@)*)@', name)
    if not m:
        return None
    return '::'.join([x for x in reversed(m.group(2).split('@')) if x] + [m.group(1)])


def member(name):
    return name.split('::')[-1] if name else None


def community_qualified(name):
    parts = [p for p in strip_templates(name or '').split('::') if p]
    while parts and parts[0] in ('RE', 'Offset'):
        parts.pop(0)
    return '::'.join(parts) or None


class Names:
    """Qualified names of decorated symbols, demangled with llvm-undname when available."""

    def __init__(self, tool=None):
        self.tool, self.cache = tool, {}

    def load(self, names):
        todo = [n for n in names if n not in self.cache and n.startswith('?')]
        if todo and self.tool:
            out = subprocess.run([self.tool] + todo, capture_output=True, text=True, timeout=60).stdout
            blocks = [b.split('\n') for b in out.strip().split('\n\n')]
            for block in blocks:
                if len(block) >= 2 and not block[1].startswith('error'):
                    self.cache[block[0]] = qualified(block[1])
        for n in names:
            # Undecorated names (extern "C", tests) are their own qualified name; compiler-made
            # names such as __real@ or $unwind$ are never bound by name.
            plain = n if re.fullmatch(r'[A-Za-z_]\w*', n) and not n.startswith('__') else None
            self.cache.setdefault(n, fallback_qualified(n) if n.startswith('?') else plain)

    def __call__(self, name):
        self.load([name])
        return self.cache.get(name)


def defined_functions(obj):
    """{name: section} for external symbols at offset 0 of a code section (comparable functions)."""
    out = {}
    for sym in obj.symbols.values():
        if sym.storage == STORAGE_EXTERNAL and sym.section > 0 and sym.value == 0 \
                and obj.section(sym.section).flags & SCN_CNT_CODE:
            out[sym.name] = sym.section
    return out


def outgoing(obj, section):
    """[(relocation, target symbol)] in `section` whose target lies outside it."""
    sec = obj.section(section)
    out = []
    for rel in sec.relocs:
        target = obj.symbols[rel.symbol]
        if target.section != section:
            out.append((rel, target))
    return out


def by_position(image, fn_rva, rel):
    """The RVA the target's own field at the relocation's offset encodes, or None."""
    if image is None:
        return None
    try:
        field = image.read(fn_rva + rel.offset, 4, 'bind')[1]
    except Exception:
        return None
    if rel.kind in REL32_TAIL:
        (disp,) = struct.unpack('<i', field)
        return fn_rva + rel.offset + 4 + REL32_TAIL[rel.kind] + disp
    if rel.kind == ADDR32NB:
        return struct.unpack('<I', field)[0]
    return None


def load_hints(task_dir):
    path = Path(task_dir) / HINTS
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f'{path}: must be a JSON object of name -> RVA')
    return {str(k): parse_rva(v) for k, v in raw.items() if not str(k).startswith('_')}


def pack_references(repo, fn):
    """[(target rva, [community qualified names])] of a function's pack, or []."""
    if not fn.get('pack'):
        return []
    path = Path(repo) / fn['pack'] / 'pack.json'
    if not path.is_file():
        return []
    out = []
    for r in json.loads(path.read_text()).get('references', []):
        names = [community_qualified(c['name']) for c in r.get('community_names', [])
                 if c.get('kind') not in ('vtable', 'rtti', 'nirtti')]
        out.append((r['target_rva'], [n for n in names if n]))
    return out


def bind(task_dir, obj_path, image_path=None, objdump=None, repo=REPO):
    """Update task.json and symbols.json in place; returns a report dict (see `describe`)."""
    task_dir = Path(task_dir)
    task = json.loads((task_dir / 'task.json').read_text())
    smap_path = task_dir / task.get('symbols', 'symbols.json')
    smap = json.loads(smap_path.read_text())
    if task.get('symbols', 'symbols.json').startswith('reports/'):
        raise ValueError('bind edits only a private task symbol map, not the repository map')
    symbols = smap.setdefault('symbols', {})
    obj = CoffObject(Path(obj_path).read_bytes())
    image = PeImage(Path(image_path).read_bytes()) if image_path and Path(image_path).is_file() else None
    hints = load_hints(task_dir)
    names = Names(find_undname(objdump))
    defined = defined_functions(obj)
    names.load(list(defined) + [s.name for s in obj.symbols.values()] + list(hints))
    report = {'functions': [], 'references': [], 'unbound_functions': [], 'unbound_references': [],
              'renamed': [], 'changed': False}

    def hint_for(name):
        if name in hints:
            return hints[name]
        q = names(name)
        return hints.get(q) if q else None

    taken = set()
    for fn in task['functions']:
        rva = parse_rva(fn['rva'])
        old = fn.get('symbol') or ''
        community = community_qualified(fn.get('community_name'))
        how, new = None, None
        hinted = [n for n, r in hints.items() if r == rva]
        for h in hinted:
            hits = [d for d in defined if d == h or names(d) == h]
            if len(hits) == 1:
                how, new = 'hint', hits[0]
                break
        if new is None and old in defined:
            how, new = 'kept', old
        if new is None and community:
            hits = [d for d in defined if names(d) == community and d not in taken]
            if len(hits) == 1:
                how, new = 'community name', hits[0]
        if new is None and community:
            hits = [d for d in defined if member(names(d)) == member(community) and d not in taken]
            if len(hits) == 1:
                how, new = 'member name', hits[0]
        if new is None:
            candidates = sorted(d for d in defined if d not in taken)
            report['unbound_functions'].append({'rva': hex(rva), 'community_name': fn.get('community_name'),
                                                'symbol': old, 'defined_in_object': candidates[:12]})
            continue
        taken.add(new)
        if new != old:
            if old and not old.startswith(UNBOUND):
                report['renamed'].append({'rva': hex(rva), 'old': old, 'new': new})
                if symbols.get(old, {}).get('rva') == rva:
                    del symbols[old]
            fn['symbol'] = new
            report['changed'] = True
        entry = {'rva': rva, 'size': parse_rva(fn['size'])}
        if symbols.get(new) != entry:
            symbols[new] = entry
            report['changed'] = True
        report['functions'].append({'rva': hex(rva), 'symbol': new, 'how': how})

    compared = {fn['symbol']: fn for fn in task['functions'] if fn['symbol'] in defined}
    own = set(compared)
    for name, fn in compared.items():
        fn_rva = parse_rva(fn['rva'])
        refs = pack_references(repo, fn)
        known = {r for r, _ in refs}
        for rel, target in outgoing(obj, defined[name]):
            ref = target.name
            if ref in symbols or ref in own:
                continue
            how, value = None, hint_for(ref)
            if value is not None:
                how = 'hint'
            if value is None:
                pos = by_position(image, fn_rva, rel)
                if pos is not None and pos in known:
                    how, value = 'position', pos
            if value is None:
                q = names(ref)
                for key in (q, member(q)):
                    if not key:
                        continue
                    hits = {r for r, cns in refs for c in cns if (c == key if key == q else member(c) == key)}
                    if len(hits) == 1:
                        how, value = ('community name' if key == q else 'member name'), hits.pop()
                        break
            if value is None:
                if ref not in report['unbound_references']:
                    report['unbound_references'].append(ref)
                continue
            symbols[ref] = {'rva': value, 'size': None}
            report['references'].append({'symbol': ref, 'rva': hex(value), 'how': how})
            report['changed'] = True
    if report['changed']:
        (task_dir / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
        smap_path.write_text(json.dumps(smap, indent=2) + '\n')
    return report


def describe(report, task_dir):
    """Short lines for the attempt output: what was bound, renamed or is still missing, and where to fix it."""
    lines = []
    bound = [f for f in report['functions'] if f['how'] != 'kept'] + report['references']
    if bound:
        lines.append('  bound: ' + '; '.join(
            f'{b.get("rva")} {"<-" if "symbol" in b else ""} {b["symbol"][:60]} ({b["how"]})' for b in bound[:6])
            + (f' ... {len(bound) - 6} more' if len(bound) > 6 else ''))
    for r in report['renamed']:
        lines.append(f'  decorated name changed for {r["rva"]}: {r["old"]} -> {r["new"]}')
    hints = Path(task_dir) / HINTS
    for f in report['unbound_functions']:
        lines.append(f'  UNBOUND function {f["rva"]} ({f["community_name"]}): no unique definition in the object; '
                     f'add {{"<decorated or Class::Method name>": "{f["rva"]}"}} to {hints}')
        if f['defined_in_object']:
            lines.append('    defined in object: ' + ', '.join(f['defined_in_object'][:6]))
    for name in report['unbound_references']:
        lines.append(f'  UNBOUND reference {name}: add {{"{name}": "0x<rva from the pack table>"}} to {hints}')
    return lines


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--task', required=True)
    p.add_argument('--object', default=None, help='Default: the newest attempts/<NNN>/candidate.obj')
    p.add_argument('--image', default=None, help='Default: .local/verifier/config.json "image"')
    a = p.parse_args(argv)
    task_dir = Path(a.task)
    obj = a.object
    if obj is None:
        objs = sorted(task_dir.glob('attempts/[0-9][0-9][0-9]/candidate.obj'))
        if not objs:
            raise SystemExit(f'no attempts/*/candidate.obj under {task_dir}; pass --object')
        obj = objs[-1]
    config = {}
    cfg = REPO / '.local/verifier/config.json'
    if cfg.is_file():
        config = json.loads(cfg.read_text())
    report = bind(task_dir, obj, a.image or config.get('image'), config.get('objdump'))
    print('\n'.join(describe(report, task_dir)) or '  nothing to bind')
    return 1 if report['unbound_functions'] or report['unbound_references'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
