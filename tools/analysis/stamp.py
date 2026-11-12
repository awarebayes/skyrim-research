"""Stamp a solved function onto the other members of its cluster ("solve one, stamp the cluster").

Given an exemplar (an accepted or passing function) and its masked cluster
(`tools/analysis/clusters.py`), generate candidate source and task directories for the other
members, in the formats `tools/verifier/attempt` and `tools/lint_reconstruction.py` expect. The
comparator stays the only judge: a stamped unit is a candidate, nothing more.

Members of a masked cluster differ only in which symbols their reference fields name, so the
source varies in exactly those names: the class a method belongs to, the callees and globals it
references, and template arguments. Three cases (see `findings/clusters-and-inlined-helpers.md`):

- `template`: one template definition in a shared header and one explicit instantiation per member;
- `class-methods`: the exemplar's body on each member's class, one unit per class;
- `duplicate-helper`: the same source for every copy; one candidate object compared against each
  copy's RVA (comparator contract v2 needs an external symbol, so internal-linkage copies wait for
  the contract change the static initializers need).

Built-in patterns (no exemplar text needed beyond the shape, because the C++ is fixed by the ABI):
`base-dtor` (an out-of-line destructor of a root polymorphic class that only restores the
vftable pointer) and `deleting-dtor` (the compiler-generated scalar deleting destructor of such a
class, sized delete of the class size). Any other pattern is a template file written once from
the exemplar by an Engineer (`--template`, format in `TEMPLATE_HELP`).

Usage (repository root; everything written is private, under `.local/`):

    python3 tools/analysis/stamp.py params --cluster m:<id> [--pattern base-dtor|deleting-dtor] [--out <file>]
    python3 tools/analysis/stamp.py emit --cluster m:<id> --pattern <name> --exemplar 0x<rva> \
        --exemplar-unit <path> --dest .local/stamp-trial/<name> [--limit N] [--template <file>]
"""
import argparse
import collections
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

BUILD_ID = 'sse-steam-1-7-104'
RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
EVIDENCE = 'findings/clusters-and-inlined-helpers.md'
GENERATOR = 'tools/analysis/stamp.py'
DEFAULT_OUT = REPO / '.local/analysis'
SIZED_DELETE = '??3@YAXPEAX_K@Z'

TEMPLATE_HELP = """A template file is JSON: {"template_schema": 1, "pattern": "<name>", "case": "class-methods",
"header": "<text>", "source": "<text>", "functions": [{"symbol": "<decorated, with placeholders>",
"qualified": "<Class::method>"}], "symbols": {"<decorated name>": "column:<hex offset>"}} where text may
use {Class} {Leaf} {NsOpen} {NsClose} {Mangled} {Base} {BaseLeaf} {BaseMangled} {Rva} {Size}
{Cluster} {Exemplar} {ExemplarUnit}, {col:<hex offset>} (the member's target name in that
reference column, slot suffix dropped) and any key of "members": {"0x<rva>": {"<Key>": "<value>"}},
which also restricts the output to the members it lists."""


# --- MSVC type names from RTTI -------------------------------------------------------------------

class Unsupported(ValueError):
    pass


BUILTIN = {'H': 'int', 'I': 'unsigned int', 'D': 'char', 'C': 'signed char', 'E': 'unsigned char',
           'F': 'short', 'G': 'unsigned short', 'J': 'long', 'K': 'unsigned long', 'M': 'float', 'N': 'double',
           'X': 'void', '_N': 'bool', '_J': 'long long', '_K': 'unsigned long long', '_W': 'wchar_t'}


class TypeName:
    """A class name parsed from an RTTI type descriptor name such as `.?AV?$Foo@VBar@@$0BA@@NS@@`."""

    def __init__(self, keyword, parts, args, mangled, decls):
        self.keyword = keyword          # 'class' or 'struct'
        self.parts = parts              # outermost namespace first; the last part may hold <args>
        self.args = args                # template arguments as C++ text, or None
        self.mangled = mangled          # decorated class name with the closing '@@' (for ??_7 / ??1)
        self.decls = decls              # forward declarations the arguments need: [(keyword, [parts])]

    @property
    def leaf(self):
        return self.parts[-1]

    @property
    def namespaces(self):
        return self.parts[:-1]

    @property
    def qualified(self):
        q = '::'.join(self.parts)
        return q + ('<%s>' % ', '.join(self.args) if self.args is not None else '')

    @property
    def template(self):
        return self.args is not None


def _number(s, i):
    """MSVC encoded integer at s[i:] -> (value, next index)."""
    neg = False
    if s[i] == '?':
        neg, i = True, i + 1
    if s[i].isdigit():
        return (-(int(s[i]) + 1) if neg else int(s[i]) + 1), i + 1
    v = 0
    while s[i] != '@':
        c = s[i]
        if not 'A' <= c <= 'P':
            raise Unsupported('integer encoding')
        v = v * 16 + ord(c) - ord('A')
        i += 1
    return (-v if neg else v), i + 1


def _name(s, i, decls, backrefs):
    """A possibly qualified, possibly template name ending in '@@' -> (parts, args, next index)."""
    parts = []
    args = None
    first = True
    while True:
        if s.startswith('@', i):
            return list(reversed(parts)), args, i + 1
        if s[i].isdigit():
            parts.append(backrefs[int(s[i])])
            i += 1
        elif s.startswith('?$', i):
            j = s.index('@', i + 2)
            tname = s[i + 2:j]
            sub_backrefs = [tname]
            targs, i = _args(s, j + 1, decls, sub_backrefs)
            if first:
                args = targs
                parts.append(tname)
            else:
                parts.append('%s<%s>' % (tname, ', '.join(targs)))
        elif s.startswith('?A0x', i) or s.startswith('?', i):
            raise Unsupported('anonymous namespace or special name')
        else:
            j = s.index('@', i)
            part = s[i:j]
            if not re.fullmatch(r'[A-Za-z_]\w*', part):
                raise Unsupported('name part %r' % part)
            parts.append(part)
            if len(backrefs) < 10:
                backrefs.append(part)
            i = j + 1
        first = False


def _type(s, i, decls, backrefs):
    for code in sorted(BUILTIN, key=len, reverse=True):
        if s.startswith(code, i):
            return BUILTIN[code], i + len(code)
    if s[i] in 'VU':
        keyword = 'class' if s[i] == 'V' else 'struct'
        parts, args, j = _name(s, i + 1, decls, backrefs)
        if args is not None:
            decls.append(('template:%s:%s' % (','.join(param_kinds(args)), keyword), parts))
            return '%s<%s>' % ('::'.join(parts), ', '.join(args)), j
        decls.append((keyword, parts))
        return '::'.join(parts), j
    if s.startswith('W4', i):
        parts, args, j = _name(s, i + 2, decls, backrefs)
        if args is not None:
            raise Unsupported('templated enum')
        decls.append(('enum', parts))
        return '::'.join(parts), j
    if s.startswith('PEA', i) or s.startswith('PEB', i):
        inner, j = _type(s, i + 3, decls, backrefs)
        return ('const ' if s[i + 2] == 'B' else '') + inner + '*', j
    raise Unsupported('type code at %r' % s[i:i + 6])


def param_kinds(args):
    # The decorated class name does not encode a non-type parameter's type; int is the plain choice.
    return ['int' if a.lstrip('-').isdigit() else 'class' for a in args]


def _args(s, i, decls, backrefs):
    out = []
    while not s.startswith('@', i):
        if s.startswith('$0', i):
            v, i = _number(s, i + 2)
            out.append(str(v))
        else:
            t, i = _type(s, i, decls, backrefs)
            out.append(t)
    return out, i + 1


def parse_type_descriptor(td):
    """TypeName for `.?AV...@@`/`.?AU...@@`; Unsupported for shapes this generator does not write."""
    if not (td.startswith('.?AV') or td.startswith('.?AU')) or not td.endswith('@@'):
        raise Unsupported('not a class type descriptor')
    keyword = 'class' if td[3] == 'V' else 'struct'
    body = td[4:]
    decls = []
    try:
        parts, args, end = _name(body, 0, decls, [])
    except (IndexError, ValueError) as exc:
        if isinstance(exc, Unsupported):
            raise
        raise Unsupported('unparsed name') from exc
    if end != len(body) - 1 and end != len(body):
        raise Unsupported('trailing characters')
    return TypeName(keyword, parts, args, body, decls)


def decorated(kind, tn):
    """Decorated names MSVC x64 gives these members of a class whose dtor is public and virtual."""
    if kind == 'vftable':
        return '??_7%s6B@' % tn.mangled
    if kind == 'dtor':
        return '??1%sUEAA@XZ' % tn.mangled
    if kind == 'deleting-dtor':
        return '??_G%sUEAAPEAXI@Z' % tn.mangled
    raise ValueError(kind)


# --- areas, as tools/ghidra/export_pack.py assigns them --------------------------------------------

def area_for(leaf):
    """The prefix rule of reconstruction/README.md; None when no rule covers the class."""
    try:
        sys.path.insert(0, str(REPO / 'tools'))
        sys.path.insert(0, str(REPO / 'tools' / 'ghidra'))
        import export_pack
        return export_pack.area_for(leaf)
    except Exception:
        return None


# --- parameter tables ------------------------------------------------------------------------------

def load_cluster(out_dir, cid):
    for line in open(Path(out_dir) / 'clusters.jsonl'):
        if line.startswith('{"cluster": "%s"' % cid):
            return json.loads(line)
    raise SystemExit('cluster %s not found in %s' % (cid, out_dir))


def rtti_tables(cfg_path):
    """{vftable rva: (type descriptor name, col offset)}, {td: ancestors}, {vftable rva: slots}."""
    import imagemodel
    cfg = imagemodel.load_config(cfg_path)
    im = imagemodel.open_image(cfg, cfg['export'], with_names=False)
    return im


def params_dtor_family(im, base_cluster, deleting_cluster):
    """Parameter rows for the base-dtor / deleting-dtor pair.

    Kind `root`: a root polymorphic class X whose functions store X's own vftable; one unit
    `X::~X() {}` yields both the out-of-line destructor (compared when exactly one base-dtor member
    stores that vftable) and the scalar deleting destructor (slot 0 of X's vftable).
    Kind `derived`: a deleting destructor at slot 0 of class D's vftable that stores the vftable of
    an RTTI base B: D's own store was dead and removed, so the source is `D : B` with an empty
    destructor; only the deleting destructor is compared (D's base-dtor member cannot be told apart
    from B's and its siblings', which store the same vftable).
    """
    base_by_vft = collections.defaultdict(list)
    for m in (base_cluster or {}).get('member_list', []):
        base_by_vft[int(m['targets'][0][2], 16)].append(m)
    del_by_vft = collections.defaultdict(list)
    for m in (deleting_cluster or {}).get('member_list', []):
        del_by_vft[int(m['targets'][0][2], 16)].append(m)
    slot0 = {}
    for v, slots in im.vtables.items():
        c = im.class_of_vtable.get(v)
        if c and c[1] == 0 and slots:
            slot0.setdefault(slots[0], v)
    rows = []
    reasons = collections.Counter()

    def named(row, td, prefix=''):
        tn = parse_type_descriptor(td)
        row[prefix + 'class'] = tn.qualified
        row[prefix + 'type_descriptor'] = td
        row[prefix + 'template'] = tn.template
        return tn

    for vft in sorted(set(base_by_vft) | set(del_by_vft)):
        c = im.class_of_vtable.get(vft)
        own = [m['rva'] for m in del_by_vft.get(vft, []) if slot0.get(int(m['rva'], 16)) == vft]
        others = [m['rva'] for m in del_by_vft.get(vft, []) if slot0.get(int(m['rva'], 16)) not in (None, vft)]
        orphans = [m['rva'] for m in del_by_vft.get(vft, []) if slot0.get(int(m['rva'], 16)) is None]
        bases = [m['rva'] for m in base_by_vft.get(vft, [])]
        row = {'kind': 'root', 'vftable': '0x%x' % vft, 'base_dtor': bases if len(bases) == 1 else [],
               'base_dtor_candidates': len(bases), 'deleting_dtor': own}
        if not c:
            row['skip'] = 'vftable without a complete object locator'
        elif c[1] != 0:
            row['skip'] = 'secondary vftable'
        elif not own and not row['base_dtor']:
            row['skip'] = 'only derived classes use this vftable'
        else:
            try:
                tn = named(row, c[0])
                row['area'] = area_for(tn.leaf)
                row['symbols'] = {decorated('vftable', tn): '0x%x' % vft}
                if row['base_dtor']:
                    row['symbols'][decorated('dtor', tn)] = row['base_dtor'][0]
                if own:
                    row['symbols'][decorated('deleting-dtor', tn)] = own[0]
            except Unsupported as exc:
                row['skip'] = 'name: %s' % exc
        reasons['root: ' + row.get('skip', 'usable')] += 1
        rows.append(row)
        for rva in orphans:
            reasons['deleting dtor in no primary vftable slot 0'] += 1
        for rva in others:
            d_vft = slot0[int(rva, 16)]
            dc = im.class_of_vtable.get(d_vft)
            drow = {'kind': 'derived', 'vftable': '0x%x' % d_vft, 'stored_vftable': '0x%x' % vft,
                    'base_dtor': [], 'deleting_dtor': [rva]}
            if not c or c[1] != 0:
                drow['skip'] = 'stored vftable is not a primary vftable'
            elif c[0] not in im.ancestors.get(dc[0], []):
                drow['skip'] = 'stored vftable is not an RTTI base of the owner'
            else:
                try:
                    tn = named(drow, dc[0])
                    named(drow, c[0], 'base_')
                    drow['area'] = area_for(tn.leaf)
                    drow['symbols'] = {decorated('deleting-dtor', tn): rva,
                                       decorated('vftable', parse_type_descriptor(c[0])): '0x%x' % vft}
                except Unsupported as exc:
                    drow['skip'] = 'name: %s' % exc
            reasons['derived: ' + drow.get('skip', 'usable')] += 1
            rows.append(drow)
    return rows, reasons


# --- emission --------------------------------------------------------------------------------------

def ns_wrap(tn, body):
    if not tn.namespaces:
        return body
    opens = ''.join('namespace %s {\n' % n for n in tn.namespaces)
    closes = ''.join('}\n' for _ in tn.namespaces)
    return opens + body + closes


def forward_decls(tn):
    out = []
    seen = set()
    for keyword, parts in tn.decls:
        key = (keyword, tuple(parts))
        if key in seen:
            continue
        seen.add(key)
        if keyword == 'enum':
            decl = 'enum class %s : int;' % parts[-1]
        elif keyword.startswith('template:'):
            _, kinds, kw = keyword.split(':')
            decl = 'template <%s> %s %s;' % (', '.join(kinds.split(',')), kw, parts[-1])
        else:
            decl = '%s %s;' % (keyword, parts[-1])
        for n in reversed(parts[:-1]):
            decl = 'namespace %s { %s }' % (n, decl)
        out.append(decl)
    return out


def dtor_unit(tn, row, cluster_ids, exemplar, exemplar_unit, model='tools/analysis/stamp.py'):
    """(header text, source text, compared functions) for a root polymorphic class's destructor."""
    leaf = tn.leaf
    compared = []
    if row.get('base_dtor'):
        compared.append(('dtor', row['base_dtor'][0], 11))
    if row.get('deleting_dtor'):
        compared.append(('deleting-dtor', row['deleting_dtor'][0], 43))
    rva_lines = ''.join('//   RVA %s, %d bytes: %s\n' % (rva, size, {
        'dtor': '%s::~%s' % (tn.qualified, leaf), 'deleting-dtor': 'scalar deleting destructor of %s' % tn.qualified}[k])
        for k, rva, size in compared)
    origin = 'EXE_RTTI'
    fwd = forward_decls(tn)
    header = (
        '// %s stand-in for its stamped destructor (build %s).\n'
        '//\n'
        '// Labels: v2\n'
        '// Source exposure: binary-analysis (the pinned image\'s RTTI and the shape of the stamped functions).\n'
        '// Generated by %s from exemplar %s (%s) for clusters %s; review the exemplar once\n'
        '// and the parameter table for the rest (findings/clusters-and-inlined-helpers.md).\n'
        '// %s: %s; the class name is the image\'s RTTI type name\n'
        '// %s::~%s: GUESS(medium); the compared code only restores this class\'s vftable pointer,\n'
        '// which is what the destructor of a root polymorphic class with no other members to destroy does\n'
        '// The class\'s other virtual functions and members are unknown and not needed by the compared code.\n'
        '#pragma once\n\n' % (tn.qualified, BUILD_ID, GENERATOR, exemplar, exemplar_unit, ', '.join(cluster_ids),
                              tn.qualified if not tn.template else '%s and its template arguments' % tn.qualified,
                              origin, tn.qualified, leaf))
    for d in fwd:
        header += d + '\n'
    if fwd:
        header += '\n'
    if tn.template:
        params = ', '.join('class T%d' % i for i in range(len(tn.args)))
        body = 'template <%s>\n%s %s {\npublic:\n    virtual ~%s();\n};\n\ntemplate <%s>\n%s<%s>::~%s() {}\n' % (
            params, tn.keyword, leaf, leaf, params, leaf, ', '.join('T%d' % i for i in range(len(tn.args))), leaf)
        if any(a.lstrip('-').isdigit() for a in tn.args):
            raise Unsupported('non-type template argument')
    else:
        body = '%s %s {\npublic:\n    virtual ~%s();\n};\n' % (tn.keyword, leaf, leaf)
    header += ns_wrap(tn, body)
    source = (
        '// %s destructor, build %s. Compared functions:\n%s'
        '//\n'
        '// Labels: v2\n'
        '// Evidence: %s.\n'
        '// Source exposure: binary-analysis. Drafted by %s (generated, no model) from exemplar\n'
        '// %s by cluster; the exemplar is %s.\n'
        '// A byte match shows that this source and recipe produce the checked code; it does not verify\n'
        '// the class name, that these functions are this class\'s destructors, or the original source.\n'
        '// Recipe: %s (compile this file alone, /Gy required).\n'
        '// %s::~%s: GUESS(medium)\n'
        '#include "%s.h"\n\n' % (tn.qualified, BUILD_ID, rva_lines, EVIDENCE, GENERATOR, exemplar, exemplar_unit,
                                 RECIPE, tn.qualified, leaf, leaf))
    if tn.template:
        source += ns_wrap(tn, 'template %s %s<%s>;\n' % (tn.keyword, leaf, ', '.join(tn.args)))
    else:
        source += ns_wrap(tn, '%s::~%s() {}\n' % (leaf, leaf))
    return header, source, compared


def task_json(task_id, unit_cpp, functions, symbols_rel='symbols.json', cluster_ids=(), exemplar=None):
    return {'task_id': task_id, 'build_id': BUILD_ID, 'compiled': unit_cpp, 'recipe': RECIPE, 'symbols': symbols_rel,
            'functions': functions, 'max_attempts': 2 * len(functions),
            'export': {'generator': GENERATOR, 'task_schema': 1, 'unit_already_records': [],
                       'stamp': {'clusters': list(cluster_ids), 'exemplar': exemplar}}}


def symbols_json(symbols):
    return {'schema': 1, 'build_id': BUILD_ID,
            'symbols': {name: {'rva': int(rva, 16) if isinstance(rva, str) else rva, 'size': size}
                        for name, (rva, size) in symbols.items()}, 'folds': []}


def emit_dtor_family(rows, dest, cluster_ids, exemplar, exemplar_unit, limit=None, delete_rva=None,
                     want_template=None, kinds=None):
    """Write units under dest/reconstruction and tasks under dest/tasks; return the emitted list."""
    dest = Path(dest)
    emitted = []
    families = collections.defaultdict(list)
    for row in rows:
        if row.get('skip') or not row.get('area'):
            continue
        tn = parse_type_descriptor(row['type_descriptor'])
        if want_template is not None and tn.template != want_template:
            continue
        if row.get('kind') == 'derived':
            if tn.template or (kinds is not None and 'derived' not in kinds):
                continue
            if limit is not None and len(emitted) >= limit:
                continue
            try:
                header, source, compared = derived_unit(tn, parse_type_descriptor(row['base_type_descriptor']), row,
                                                        cluster_ids, exemplar, exemplar_unit)
            except Unsupported:
                continue
            emitted.append(write_unit(dest, row['area'], tn.leaf, header, source, compared, tn, row, delete_rva,
                                      cluster_ids, exemplar))
            continue
        if kinds is not None and 'root' not in kinds:
            continue
        if tn.template:
            families[(tn.keyword, tuple(tn.namespaces), tn.leaf, len(tn.args))].append((tn, row))
            continue
        if limit is not None and len(emitted) >= limit:
            continue
        try:
            header, source, compared = dtor_unit(tn, row, cluster_ids, exemplar, exemplar_unit)
        except Unsupported:
            continue
        emitted.append(write_unit(dest, row['area'], tn.leaf, header, source, compared, tn, row, delete_rva,
                                  cluster_ids, exemplar))
    for key, members in sorted(families.items(), key=lambda kv: -len(kv[1])):
        if limit is not None and len(emitted) >= limit:
            break
        tn0, row0 = members[0]
        if len({tuple(param_kinds(tn.args)) for tn, _ in members}) != 1:
            continue
        # One unit per family: the template once, one explicit instantiation per member.
        fwd, compared, inst = [], [], []
        for tn, row in members:
            fwd += [d for d in forward_decls(tn) if d not in fwd]
            inst.append('template %s %s<%s>;' % (tn.keyword, tn.leaf, ', '.join(tn.args)))
            for k, rva, size in dtor_unit(tn, row, cluster_ids, exemplar, exemplar_unit)[2]:
                compared.append((k, rva, size, tn))
        header_text = family_header(tn0, fwd, len(members), cluster_ids, exemplar, exemplar_unit)
        rva_lines = ''.join('//   RVA %s, %d bytes: %s\n' % (rva, size, ('%s::~%s' % (tn.qualified, tn.leaf)) if k == 'dtor'
                                                               else 'scalar deleting destructor of %s' % tn.qualified)
                            for k, rva, size, tn in compared)
        source = (
            '// %s destructors, build %s. Compared functions:\n%s'
            '//\n'
            '// Labels: v2\n'
            '// Evidence: %s.\n'
            '// Source exposure: binary-analysis. Drafted by %s (generated, no model) from exemplar\n'
            '// %s by cluster; the exemplar is %s.\n'
            '// A byte match shows that this source and recipe produce the checked code; it does not verify\n'
            '// the class names or the original source.\n'
            '// Recipe: %s (compile this file alone, /Gy required).\n'
            '// %s::~%s: GUESS(medium)\n'
            '#include "%s.h"\n\n' % (tn0.leaf, BUILD_ID, rva_lines, EVIDENCE, GENERATOR, exemplar, exemplar_unit,
                                     RECIPE, tn0.leaf, tn0.leaf, tn0.leaf))
        source += ns_wrap(tn0, '\n'.join(inst) + '\n')
        emitted.append(write_unit(dest, row0['area'], tn0.leaf, header_text, source,
                                  [(k, rva, size) for k, rva, size, _ in compared], None,
                                  {'symbols': {s: r for _, row in members for s, r in row['symbols'].items()}},
                                  delete_rva, cluster_ids, exemplar, family=[tn.qualified for tn, _ in members]))
    return emitted


def base_standin(btn):
    """Declaration of the RTTI base whose destructor the derived class's code inlines."""
    if btn.template:
        params = ', '.join('%s T%d' % (k, i) for i, k in enumerate(param_kinds(btn.args)))
        body = 'template <%s>\n%s %s {\npublic:\n    virtual ~%s() {}\n};\n' % (params, btn.keyword, btn.leaf, btn.leaf)
    else:
        body = '%s %s {\npublic:\n    virtual ~%s() {}\n};\n' % (btn.keyword, btn.leaf, btn.leaf)
    return ns_wrap(btn, body)


def derived_unit(tn, btn, row, cluster_ids, exemplar, exemplar_unit):
    """(header, source, compared) for a class whose deleting destructor inlines its base's destructor."""
    leaf = tn.leaf
    rva = row['deleting_dtor'][0]
    fwd = []
    for d in forward_decls(btn) + forward_decls(tn):
        if d not in fwd:
            fwd.append(d)
    header = (
        '// %s stand-in for its stamped deleting destructor (build %s).\n'
        '//\n'
        '// Labels: v2\n'
        '// Source exposure: binary-analysis (the pinned image\'s RTTI and the shape of the stamped function).\n'
        '// Generated by %s from exemplar %s (%s) for clusters %s; review the exemplar once\n'
        '// and the parameter table for the rest (findings/clusters-and-inlined-helpers.md).\n'
        '// %s, %s: EXE_RTTI; class names and the base relation from the image\'s RTTI\n'
        '// %s::~%s: GUESS(medium); the compared deleting destructor restores only the base\'s vftable\n'
        '// pointer, so this class\'s own destructor body is empty and its vftable store was removed\n'
        '// %s: STANDIN EXE_RTTI; only an inline virtual destructor is declared\n'
        '// Other virtual functions and members of both classes are unknown and not needed by the compared code.\n'
        '#pragma once\n\n' % (tn.qualified, BUILD_ID, GENERATOR, exemplar, exemplar_unit, ', '.join(cluster_ids),
                              tn.qualified, btn.qualified, tn.qualified, leaf, btn.qualified))
    if fwd:
        header += '\n'.join(fwd) + '\n\n'
    header += base_standin(btn) + '\n'
    header += ns_wrap(tn, '%s %s : public %s {\npublic:\n    ~%s() override;\n};\n' % (tn.keyword, leaf, btn.qualified, leaf))
    source = (
        '// %s destructor, build %s. Compared functions:\n'
        '//   RVA %s, 43 bytes: scalar deleting destructor of %s\n'
        '//\n'
        '// Labels: v2\n'
        '// Evidence: %s.\n'
        '// Source exposure: binary-analysis. Drafted by %s (generated, no model) from exemplar\n'
        '// %s by cluster; the exemplar is %s.\n'
        '// A byte match shows that this source and recipe produce the checked code; it does not verify\n'
        '// the class names, the base relation as written or the original source.\n'
        '// Recipe: %s (compile this file alone, /Gy required). The out-of-line destructor this\n'
        '// file also defines is not compared: several functions in the image store the same vftable.\n'
        '// %s::~%s: GUESS(medium)\n'
        '#include "%s.h"\n\n' % (tn.qualified, BUILD_ID, rva, tn.qualified, EVIDENCE, GENERATOR, exemplar,
                                 exemplar_unit, RECIPE, tn.qualified, leaf, leaf))
    source += ns_wrap(tn, '%s::~%s() {}\n' % (leaf, leaf))
    return header, source, [('deleting-dtor', rva, 43)]


def family_header(tn0, fwd, n, cluster_ids, exemplar, exemplar_unit):
    params = ', '.join('%s T%d' % (k, i) for i, k in enumerate(param_kinds(tn0.args)))
    names = ', '.join('T%d' % i for i in range(len(tn0.args)))
    leaf = tn0.leaf
    text = (
        '// %s class template stand-in for its stamped destructors (build %s).\n'
        '//\n'
        '// Labels: v2\n'
        '// Source exposure: binary-analysis (the pinned image\'s RTTI and the shape of the stamped functions).\n'
        '// Generated by %s from exemplar %s (%s) for clusters %s; review the exemplar once\n'
        '// and the parameter table for the rest (findings/clusters-and-inlined-helpers.md).\n'
        '// %s and the %d template argument classes declared below: EXE_RTTI; names from the image\'s RTTI type names\n'
        '// %s::~%s: GUESS(medium); each instantiation\'s compared code only restores its vftable pointer\n'
        '// The template\'s other virtual functions and members are unknown and not needed by the compared code.\n'
        '#pragma once\n\n' % (leaf, BUILD_ID, GENERATOR, exemplar, exemplar_unit, ', '.join(cluster_ids), leaf, n,
                              leaf, leaf))
    if fwd:
        text += '\n'.join(fwd) + '\n\n'
    body = 'template <%s>\n%s %s {\npublic:\n    virtual ~%s();\n};\n\ntemplate <%s>\n%s<%s>::~%s() {}\n' % (
        params, tn0.keyword, leaf, leaf, params, leaf, names, leaf)
    return text + ns_wrap(tn0, body)


def write_unit(dest, area, leaf, header, source, compared, tn, row, delete_rva, cluster_ids, exemplar, family=None):
    unit_dir = dest / 'reconstruction' / area
    unit_dir.mkdir(parents=True, exist_ok=True)
    (unit_dir / ('%s.h' % leaf)).write_text(header)
    (unit_dir / ('%s.cpp' % leaf)).write_text(source)
    task_id = 'stamp-%s-%s' % (cluster_ids[0].split(':')[1][:8], leaf.lower())
    tdir = dest / 'tasks' / task_id
    tdir.mkdir(parents=True, exist_ok=True)
    by_rva = {r: s for s, r in row['symbols'].items()}
    functions = []
    for k, rva, size in compared:
        sym = by_rva.get(rva)
        functions.append({'rva': rva, 'size': size, 'symbol': sym or 'unbound:%s' % leaf,
                          'function_id': '%s-%s' % (BUILD_ID, rva), 'community_name': None,
                          'name_origin': 'GUESS', 'verdict': 'stamped', 'pack': None, 'stamp_kind': k})
    unit_cpp = 'reconstruction/%s/%s.cpp' % (area, leaf)
    (tdir / 'task.json').write_text(json.dumps(task_json(task_id, unit_cpp, functions, cluster_ids=cluster_ids,
                                                         exemplar=exemplar), indent=1) + '\n')
    syms = {}
    sizes = {f['rva']: f['size'] for f in functions}
    for s, r in row['symbols'].items():
        syms[s] = (r, sizes.get(r))
    if delete_rva:
        syms[SIZED_DELETE] = (delete_rva, None)
    (tdir / 'symbols.json').write_text(json.dumps(symbols_json(syms), indent=1) + '\n')
    brief = ['# %s (stamped)' % task_id, '',
             'Unit `%s`, recipe `%s`, budget %d attempts.' % (unit_cpp, RECIPE, 2 * len(functions)),
             'Generated by `%s` from exemplar %s by clusters %s; no Drafter.' % (GENERATOR, exemplar, ', '.join(cluster_ids)),
             'Functions: ' + ', '.join('%s (%d B, %s)' % (f['rva'], f['size'], f['stamp_kind']) for f in functions) + '.',
             'If a function fails, do not edit the unit by hand: report the reason; the pattern or the',
             'parameter row is wrong, and the fix belongs in the generator or the template.']
    if family:
        brief.append('Family members: %d instantiations.' % len(family))
    (tdir / 'BRIEF.md').write_text('\n'.join(brief) + '\n')
    return {'task': task_id, 'unit': unit_cpp, 'functions': len(functions), 'class': leaf, 'family': family}


# --- template-file patterns (class-methods from an arbitrary exemplar) -----------------------------

def fill(text, values):
    def rep(m):
        key = m.group(1)
        if key not in values:
            raise KeyError('placeholder {%s} has no value' % key)
        return str(values[key])
    return re.sub(r'\{([A-Za-z]+(?::0x[0-9a-f]+)?)\}', rep, text)


def emit_from_template(tpl, cluster, im, dest, exemplar, exemplar_unit, limit=None):
    """Units for members of a class-methods cluster from a template file; skips members whose
    owner class does not parse or whose reference columns lack a name."""
    dest = Path(dest)
    out = []
    for m in cluster['member_list']:
        if m['rva'] == exemplar:
            continue
        if limit is not None and len(out) >= limit:
            break
        if not m.get('owner'):
            continue
        vft = next((v for v, (raw, coloff) in im.class_of_vtable.items()
                    if im.display.get(raw) == m['owner'] and coloff == 0), None)
        if vft is None:
            continue
        try:
            tn = parse_type_descriptor(im.class_of_vtable[vft][0])
        except Unsupported:
            continue
        area = area_for(tn.leaf)
        if not area:
            continue
        values = {'Class': tn.qualified, 'Leaf': tn.leaf, 'Mangled': tn.mangled,
                  'NsOpen': ''.join('namespace %s {\n' % n for n in tn.namespaces),
                  'NsClose': ''.join('}\n' for _ in tn.namespaces), 'Rva': m['rva'], 'Size': m['size'],
                  'Cluster': cluster['cluster'], 'Exemplar': exemplar, 'ExemplarUnit': exemplar_unit}
        # Values no cluster table holds (a member's name and type at an offset) come per member
        # from the template file, written from the community header by the Engineer.
        values.update(tpl.get('members', {}).get(m['rva'], {}))
        if tpl.get('members') and m['rva'] not in tpl['members']:
            continue
        ok = True
        for off, kind, target, label in m['targets']:
            if not label:
                ok = False
            values['col:%s' % off] = (label or '').split(' slot ')[0]
        base = values.get('col:%s' % tpl.get('base_column', ''), '')
        values['Base'] = base
        values['BaseLeaf'] = base.split('::')[-1]
        if not ok:
            continue
        try:
            header, source = fill(tpl['header'], values), fill(tpl['source'], values)
        except KeyError:
            continue
        symbols = {}
        for f in tpl['functions']:
            symbols[fill(f['symbol'], values)] = m['rva']
        for name, col in tpl.get('symbols', {}).items():
            off = col.split(':', 1)[1]
            t = next((t for t in m['targets'] if t[0] == off), None)
            if t:
                symbols[fill(name, values)] = t[2]
        row = {'symbols': symbols}
        out.append(write_unit(dest, area, tn.leaf, header, source, [('method', m['rva'], m['size'])], tn, row, None,
                              [cluster['cluster']], exemplar))
    return out


# --- command line ----------------------------------------------------------------------------------

def cmd_params(args):
    import imagemodel
    im = rtti_tables(args.config)
    base = load_cluster(args.out_dir, args.base_cluster) if args.base_cluster else None
    dele = load_cluster(args.out_dir, args.deleting_cluster) if args.deleting_cluster else None
    rows, reasons = params_dtor_family(im, base, dele)
    if args.write:
        Path(args.write).write_text(json.dumps(rows, indent=1) + '\n')
    print(json.dumps({'rows': len(rows), 'reasons': reasons, 'usable': sum(1 for r in rows if not r.get('skip')),
                      'usable_with_area': sum(1 for r in rows if not r.get('skip') and r.get('area')),
                      'usable_templates': sum(1 for r in rows if not r.get('skip') and r.get('template'))}, indent=1))
    del imagemodel
    return 0


def cmd_emit(args):
    im = rtti_tables(args.config)
    dest = Path(args.dest)
    if args.pattern == 'dtor-family':
        base = load_cluster(args.out_dir, args.base_cluster)
        dele = load_cluster(args.out_dir, args.deleting_cluster) if args.deleting_cluster else None
        rows, _ = params_dtor_family(im, base, dele)
        delete_rva = None
        if dele:
            col = next(t for t in dele['member_list'][0]['targets'] if not (t[3] or '').startswith('vftable:'))
            delete_rva = col[2]
        ids = [base['cluster']] + ([dele['cluster']] if dele else [])
        emitted = emit_dtor_family(rows, dest, ids, args.exemplar, args.exemplar_unit, args.limit, delete_rva,
                                   want_template=None if args.templates == 'both' else args.templates == 'only',
                                   kinds=set(args.kinds.split(',')) if args.kinds else None)
    else:
        tpl = json.loads(Path(args.template).read_text())
        cluster = load_cluster(args.out_dir, args.cluster)
        emitted = emit_from_template(tpl, cluster, im, dest, args.exemplar, args.exemplar_unit, args.limit)
    (dest / 'emitted.json').write_text(json.dumps(emitted, indent=1) + '\n')
    print(json.dumps({'units': len(emitted), 'functions': sum(e['functions'] for e in emitted)}))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config', default=str(REPO / '.local/config/analysis.json'))
    ap.add_argument('--out-dir', default=str(DEFAULT_OUT), help='where clusters.py build wrote its tables')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('params', help='parameter table of the destructor family')
    p.add_argument('--base-cluster', required=True)
    p.add_argument('--deleting-cluster')
    p.add_argument('--write')
    e = sub.add_parser('emit')
    e.add_argument('--pattern', required=True, choices=['dtor-family', 'template-file'])
    e.add_argument('--base-cluster')
    e.add_argument('--deleting-cluster')
    e.add_argument('--cluster')
    e.add_argument('--template')
    e.add_argument('--templates', choices=['both', 'only', 'none'], default='both')
    e.add_argument('--kinds', help='comma-separated row kinds of the destructor family: root, derived')
    e.add_argument('--exemplar', required=True)
    e.add_argument('--exemplar-unit', required=True)
    e.add_argument('--dest', required=True)
    e.add_argument('--limit', type=int)
    args = ap.parse_args(argv)
    return {'params': cmd_params, 'emit': cmd_emit}[args.cmd](args)


if __name__ == '__main__':
    raise SystemExit(main())
