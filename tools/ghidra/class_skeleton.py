"""Header skeleton for one class from the private class table, for a Drafter to start from.

    python3 tools/ghidra/class_skeleton.py <Class> [--analysis .local/analysis] [--out <file>]

Reads `.local/analysis/classes.jsonl` (written by build_function_table.py) and prints a header:
the primary base chain as minimal stand-ins (each declaring only the virtual slots it adds), the
class itself with every slot in order (new virtuals and overrides), the object size from the
deleting destructor as a comment and a static_assert, and one `Labels: v2` line per name. A slot
name comes from a community header only where that class passed the per-class checks of
docs/resource-guidelines.md (section 2), else from meh321's list by Address Library id, else it
is an `Unk_NN` placeholder. Signatures are placeholders (`void()`): the community declaration, when
there is one, is quoted in a comment so the Drafter can restore return and parameter types.

The output names RVAs of the pinned build and community names only, no code or bytes; it is
still written under .local/ by default, since a Drafter edits it into a unit.
"""
import argparse
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def labels_for(cfg):
    return {
        'ng-slot': f'COMMUNITY(CharmedBaryon/CommonLibSSE-NG@{(cfg.get("ng_revision") or "0" * 7)[:7]}, MIT)',
        'po3-slot': f'COMMUNITY(powerof3/CommonLibSSE@{(cfg.get("po3_revision") or "0" * 7)[:7]}, GPL-3.0)',
        'meh321': f'COMMUNITY(meh321/AddressLibrary@{(cfg.get("meh321_revision") or "0" * 12)[:12]}, permission)',
    }


def load_classes(analysis):
    out = {}
    with open(Path(analysis) / 'classes.jsonl') as fh:
        for line in fh:
            c = json.loads(line)
            out[c['class']] = c
    return out


def find_class(classes, name):
    if name in classes:
        return classes[name]
    hits = [c for c in classes.values() if c.get('ng_key') == name or c['class'].split('::')[-1] == name]
    if len(hits) == 1:
        return hits[0]
    raise SystemExit(f'{name}: ' + ('ambiguous: ' + ', '.join(sorted(c['class'] for c in hits)) if hits
                                    else 'no class with a primary vftable has this name'))


def ident(name):
    """A C++ spelling of an RTTI class name: namespaces kept, template arguments folded in."""
    return '::'.join(re.sub(r'\W', '_', p).strip('_') or 'anon' for p in re.sub(r'<(.*)>', lambda m: '_' + m.group(1),
                                                                                 name).split('::'))


def chain_of(classes, cls):
    out, cur = [], cls
    while cur is not None:
        out.append(cur)
        cur = classes.get(cur['parent']) if cur.get('parent') else None
    return list(reversed(out))  # root first


def slot_plan(chain):
    """Per class of the chain: [(slot, name, source, declaration, kind)] where kind is 'new' or
    'override'. A slot keeps the name it got where it was introduced, so overrides always name
    the same virtual as the base stand-in declares."""
    names, plan, used = {}, [], {}
    for i, c in enumerate(chain):
        parent_len = len(chain[i - 1]['slots']) if i else 0
        parent = chain[i - 1]['slots'] if i else []
        rows = []
        for k, target in enumerate(c['slots']):
            if k >= parent_len:
                sn = (c.get('slot_names') or {}).get(str(k)) or (c.get('slot_names') or {}).get(k)
                if sn:
                    name, source, decl = sn['name'], sn['source'], sn.get('declaration')
                    if name.startswith('~'):
                        name = '~' + ident(c['class']).split('::')[-1]
                        if any(n.startswith('~') for n, *_ in names.values()):
                            name, source, decl = f'Unk_{k:02X}', None, None
                    elif name in used and used[name] != k:
                        name, source, decl = f'{name}_{k:02X}', 'renamed', decl
                else:
                    name, source, decl = f'Unk_{k:02X}', None, None
                used.setdefault(name, k)
                names[k] = (name, source, decl)
                rows.append((k, name, source, decl, 'new', target))
            elif target != parent[k]:
                name, source, decl = names[k]
                if name.startswith('~'):
                    name = '~' + ident(c['class']).split('::')[-1]
                rows.append((k, name, source, decl, 'override', target))
        plan.append(rows)
    return plan


def label_line(qual, source, labels, note=None):
    if source in labels:
        text = f'// {qual}: {labels[source]}'
    elif source == 'renamed':
        text = f'// {qual}: GUESS; the community name repeats at another slot, suffixed with this slot'
        note = None
    else:
        text = f'// {qual}: GUESS(low); placeholder, no checked name for this slot'
        note = None
    return text + (f'; {note}' if note else '')


def clean_comment(text, limit=140):
    text = re.sub(r'[^\x20-\x7e]', '', text or '').replace('##', '#').replace('\\', '/')
    text = re.sub(r'(?<![A-Za-z0-9_])(COMMUNITY|GUESS|EXE_RTTI|STANDIN|OBSERVED)', lambda m: m.group(1).lower(), text)
    return text[:limit]


def render_class(c, rows, parent, labels, standin, build_id, psize=8):
    """Lines for one class; psize is the sizeof the emitted parent declaration has (8 for a root:
    its vftable pointer). Returns (lines, sizeof of this declaration)."""
    full = ident(c['class'])
    ns, _, short = full.rpartition('::')
    out = []
    kind = 'STANDIN EXE_RTTI' if standin else 'EXE_RTTI'
    out.append(f'// {short}: {kind}; class name and base from the image RTTI, '
               f'{len(c["slots"])} primary vftable slots')
    if c.get('size'):
        out.append(f'// sizeof {short} 0x{c["size"]:X}: OBSERVED; size argument of operator delete in the deleting '
                   'destructor (slot 0)')
    if c.get('bases') and len(c['bases']) > len(c['chain']) - 1:
        others = [b for b in c['bases'] if b not in c['chain']]
        if others:
            out.append(f'// Other RTTI bases (not declared here; their vftable pointers lie inside the members): '
                       f'{clean_comment(", ".join(others), 400)}')
    if ns:
        out.append(f'namespace {ns}')
        out.append('{')
    base = f' : public ::{ident(parent["class"])}' if parent else ''
    out.append(f'class {short}{base}')
    out.append('{')
    out.append('public:')
    for k, name, source, decl, how, target in rows:
        qual = f'{short}::{name}'
        out.append('\t' + label_line(qual, source, labels,
                                     f'slot {k}, target 0x{target:x}' + (', inherited name' if how == 'override' else '')))
        if decl:
            out.append(f'\t// community declaration: {clean_comment(decl)}')
        if name.startswith('~'):
            out.append(f'\t{"virtual " if how == "new" else ""}{name}(){" override" if how == "override" else ""};'
                       f'  // {k:02X}')
        else:
            out.append(f'\t{"virtual " if how == "new" else ""}void {name}(){" override" if how == "override" else ""};'
                       f'  // {k:02X}')
    emitted = psize
    if c.get('size') and c['size'] > psize:
        emitted = c['size']
        off = psize
        out.append('')
        out.append(f'\t// unk{off:02X}: GUESS(low); members not recovered yet, sized so the static_assert holds')
        out.append(f'\tstd::uint8_t unk{off:02X}[0x{c["size"] - off:X}];  // {off:02X}')
    out.append('};')
    if c.get('size') and c['size'] >= psize:
        out.append(f'static_assert(sizeof({short}) == 0x{c["size"]:X});')
    elif c.get('size'):
        out.append(f'// sizeof {short} 0x{c["size"]:X} is below its base stand-in\'s; no static_assert')
    if ns:
        out.append('}')
    return out, emitted


def render(classes, name, cfg=None, build_id='sse-steam-1-7-104'):
    cfg = cfg or {}
    labels = labels_for(cfg)
    c = find_class(classes, name)
    chain = chain_of(classes, c)
    plan = slot_plan(chain)
    sources = {r[2] for rows in plan for r in rows}
    gpl = 'po3-slot' in sources
    community = sources & set(labels)
    checks = []
    for x in chain:
        for src, chk in sorted((x.get('community') or {}).items()):
            checks.append(f'{x["class"]} {src}: ' + ', '.join(
                f'{k.split("_")[0]} {chk.get(k)}' for k in ('C1_length', 'C2_range', 'C3_pattern', 'C4_size',
                                                            'rtti_name', 'base_chain'))
                          + f', passes {chk.get("passes")}')
    head = [f'// Skeleton of {ident(c["class"])} for build {build_id}, generated by tools/ghidra/class_skeleton.py '
            'from the image RTTI and vftables.',
            f'// Source exposure: {"mixed" if community else "binary-analysis"}',
            '// Labels: v2',
            '// Signatures are placeholders (void, no parameters) until the Drafter restores them from the',
            '// listing or the quoted community declaration; slot order and count come from the image.']
    if gpl:
        head.append('// Licence: this file carries declarations derived from powerof3/CommonLibSSE and is '
                    'GPL-3.0 (docs/authorizations.md).')
    if 'meh321' in sources:
        head.append('// Names marked meh321 come from his Address Library name list, used with the author\'s '
                    'permission as reported by the maintainer.')
    head.append('// Per-class checks (docs/resource-guidelines.md, section 2):')
    head += [f'//   {clean_comment(line, 300)}' for line in checks] or ['//   no community declaration joined']
    lines = head + ['#pragma once', '', '#include <cstdint>', '']
    psize = 8
    for i, x in enumerate(chain):
        parent = chain[i - 1] if i else None
        body, psize = render_class(x, plan[i], parent, labels, x is not c, build_id, psize)
        lines += body + ['']
    return '\n'.join(lines).rstrip() + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('cls')
    p.add_argument('--analysis', default=str(REPO / '.local/analysis'))
    p.add_argument('--config', default=str(REPO / '.local/config/export_pack.json'))
    p.add_argument('--out', default=None)
    a = p.parse_args(argv)
    cfg = json.loads(Path(a.config).read_text()) if Path(a.config).is_file() else {}
    meta = Path(a.analysis) / 'table-meta.json'
    if meta.is_file():
        cfg.setdefault('meh321_revision', json.loads(meta.read_text())['inputs'].get('meh321_names') or '0' * 12)
    text = render(load_classes(a.analysis), a.cls, cfg)
    if a.out:
        Path(a.out).write_text(text)
    else:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
