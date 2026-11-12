"""Clusters of functions that share code, for "solve one, stamp the cluster".

Three levels, each a partition of the population (default: `.text$mn` entries that are not
funclets or thunks, `docs/resource-guidelines.md`):

- `exact`: identical bytes over the compared range.
- `masked` (L1): identical after blanking exactly the fields the comparator compares as
  references (`tools/analysis/imagemodel.py`), with identical field layout, self-relative targets,
  unwind codes and chained entries. Members differ only in WHICH symbols they reference, so one
  source with other names compiles to each of them.
- `shape` (L2): masked plus displacements and immediates blanked: accessors of other offsets,
  constant returns of other values. Stamping across an L2 cluster also varies a member offset or a
  constant, which is a weaker claim than an L1 stamp.

Usage (repository root; outputs are game-derived and go under `.local/` only):

    python3 tools/analysis/clusters.py build [--config .local/config/analysis.json] [--out .local/analysis]
    python3 tools/analysis/clusters.py show 0x<rva> [...]       # the function's cluster, private, to the terminal
    python3 tools/analysis/clusters.py rank --exemplars .local/analysis/exemplars.tsv [--top 30]

`build` writes `clusters.jsonl` (one masked cluster of two or more members per line),
`function-clusters.tsv` (every analysed function: rva, size, masked, exact and shape cluster ids
and sizes) and `summary.json` (counts only), and prints the summary, which is sanitized: counts
and bytes, no addresses or names.
"""
import argparse
import collections
import json
from pathlib import Path
import pickle
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import imagemodel  # noqa: E402
import x64  # noqa: E402

DEFAULT_CONFIG = REPO / '.local/config/analysis.json'
DEFAULT_OUT = REPO / '.local/analysis'
DEFAULT_GROUPS = ('.text$mn', '.text$mn$00')
SIZE_BUCKETS = ((2, 2), (3, 4), (5, 9), (10, 19), (20, 99), (100, None))


def bucket(n):
    for lo, hi in SIZE_BUCKETS:
        if n >= lo and (hi is None or n <= hi):
            return '%d+' % lo if hi is None else ('%d' % lo if lo == hi else '%d-%d' % (lo, hi))
    return '1'


def in_population(name, group, groups):
    if group not in groups:
        return False
    return not (imagemodel.is_funclet_name(name) or name.startswith('thunk_'))


def partition(records, key):
    """{cluster id: [records]} by record[key], members in address order."""
    out = collections.defaultdict(list)
    for r in records:
        out[r[key]].append(r)
    for v in out.values():
        v.sort(key=lambda r: r['rva'])
    return out


def level_summary(parts):
    """Counts of one level: clusters and functions per cluster-size bucket, repeats, bytes."""
    rows = collections.OrderedDict()
    for lo, hi in SIZE_BUCKETS:
        rows[bucket(lo)] = {'clusters': 0, 'functions': 0, 'bytes': 0}
    repeats = repeat_bytes = 0
    singletons = 0
    for members in parts.values():
        n = len(members)
        if n == 1:
            singletons += 1
            continue
        row = rows[bucket(n)]
        row['clusters'] += 1
        row['functions'] += n
        row['bytes'] += sum(m['size'] for m in members)
        repeats += n - 1
        repeat_bytes += sum(m['size'] for m in members[1:])
    return {'buckets': rows, 'singletons': singletons, 'repeats': repeats, 'repeat_bytes': repeat_bytes}


def columns(members):
    """Reference columns of a masked cluster: [(field offset, kind, varies?)].

    Members of one masked cluster have the same field layout, so the i-th external target of every
    member sits at the same offset. A column that holds one target for all members is constant (the
    same callee or global everywhere); a varying column is a parameter of the stamped source.
    """
    if not members:
        return []
    first = members[0]['targets']
    out = []
    for i, (off, kind, _t) in enumerate(first):
        values = {m['targets'][i][2] for m in members if i < len(m['targets'])}
        out.append((off, kind, len(values) > 1))
    return out


def operand_columns(members):
    """Displacement and immediate columns of a shape cluster: [(offset, size, varies?)]."""
    if not members:
        return []
    first = members[0]['operands']
    out = []
    for i, (off, size, _v) in enumerate(first):
        values = {m['operands'][i][2] for m in members if i < len(m['operands'])}
        out.append((off, size, len(values) > 1))
    return out


def stamp_case(members):
    """Which stamping case a masked cluster falls in (docs: findings/clusters-and-inlined-helpers.md).

    `template`: every owned member belongs to a template instantiation (RTTI `?$`) or carries a
    template-argument community name. `class-methods`: members belong to different non-template
    classes. `duplicate-helper`: no member has an owner class and every member references the same
    targets (one source, copied per translation unit). `unowned`: none of these.
    """
    owners = [m.get('owner') for m in members]
    owned = [m for m in members if m.get('owner') or imagemodel.class_of_name(m.get('name'))]
    if owned and all(m.get('template') or '<' in (m.get('owner') or m.get('name') or '') for m in owned) \
            and len(owned) * 2 >= len(members):
        return 'template'
    classes = {m.get('owner') or imagemodel.class_of_name(m.get('name')) for m in owned}
    if len(classes) >= 2 and len(owned) * 2 >= len(members):
        return 'class-methods'
    if not any(owners):
        targets = {tuple(t[2] for t in m['targets']) for m in members}
        if len(targets) == 1:
            return 'duplicate-helper'
    return 'unowned'


def stampable(member, case, labels=()):
    """A member can be stamped when it has a class identity: an RTTI owner, a community name, or a
    vftable it stores (the destructor shapes); a duplicated helper always can (its source is the
    exemplar's, verbatim), though comparing an internal-linkage copy needs a contract change."""
    if case == 'duplicate-helper':
        return True
    return bool(member.get('owner') or member.get('name') or any(l and l.startswith('vftable:') for l in labels))


# --- shape descriptions ------------------------------------------------------------------------

def describe(insns, code, rec):
    """A plain-words description of a short exemplar, or None when no simple rule applies.

    Only shapes recognisable from opcodes are described; the caller adds the evidence (a
    community name or slot) before publishing a description.
    """
    ops = [(o, i) for o, i in insns if i.flow not in (x64.INT3, x64.NOP)]
    if not ops:
        return None
    flows = [i.flow for _, i in ops]
    opc = [i.opcode for _, i in ops]
    if flows == [x64.RET]:
        return 'empty function (returns at once)'
    if len(ops) == 2 and flows[-1] == x64.RET:
        o, i = ops[0]
        if opc[0] in ((0x8B,), (0x0F, 0xB6), (0x0F, 0xB7), (0x0F, 0xBE), (0x0F, 0xBF), (0x63,)) and i.base == 1 \
                and i.rip is None:
            return 'returns a member of `this` at offset 0x%x' % ((i.disp[2] if i.disp else 0) & 0xFFFFFFFF)
        if opc[0] in ((0x8D,),) and i.rip is not None:
            return 'returns the address of a global'
        if opc[0] in ((0x8D,),) and i.base == 1:
            return 'returns the address of a member of `this` at offset 0x%x' % ((i.disp[2] if i.disp else 0) & 0xFFFFFFFF)
        if opc[0] in ((0x8B,),) and i.rip is not None:
            return 'returns a global'
        if opc[0] in ((0x33,), (0x31,)):
            return 'returns zero'
        if opc[0][0] in range(0xB0, 0xC0):
            return 'returns a constant'
        if opc[0] in ((0x0F, 0xB6),):
            return 'returns a byte member'
    if len(ops) == 1 and flows[0] == x64.JMP and ops[0][1].rel and ops[0][1].rel[1] == 4:
        return 'tail call to another function (thunk shape)'
    if len(ops) == 2 and flows[1] == x64.JMP and opc[0] in ((0x83,), (0x81,), (0x8D,)):
        return 'adjusts `this` and tail-calls (adjustor thunk shape)'
    if len(ops) == 2 and flows[1] == x64.JMP and ops[0][1].rip is not None:
        return 'loads a global and tail-calls'
    if len(ops) == 2 and flows[1] == x64.RET and opc[0] in ((0x88,), (0x89,), (0xC6,), (0xC7,)) and ops[0][1].base == 1:
        return 'stores to a member of `this` and returns'
    # A deleting destructor: calls the destructor, tests bit 0 of the flags argument, frees.
    tests_bit0 = any(i.opcode == (0xF6,) and (i.reg & 7) == 0 and i.imm and code[o + i.imm[0]] == 1
                     for o, i in ops)
    calls = sum(1 for f in flows if f in (x64.CALL, x64.ICALL))
    if tests_bit0 and calls >= 1 and len(ops) <= 16:
        return 'deleting destructor shape (destroy, then free when bit 0 of the flags is set)'
    locks = sum(1 for o, _ in ops if code[o] == 0xF0)
    if locks and len(ops) <= 20 and any(i.flow in (x64.ICALL,) for _, i in ops):
        return 'reference-count release shape (locked decrement, virtual call when it reaches zero)'
    return None


# --- building ------------------------------------------------------------------------------------

def analyse_population(im, groups, progress=True):
    records = []
    errors = collections.Counter()
    t0 = time.time()
    for i, (rva, size, name) in enumerate(im.funcs):
        if not in_population(name, im.group[i], groups):
            continue
        r = im.analyse(i)
        if 'error' in r:
            errors[r['error'].split(':')[0]] += 1
            continue
        insns, code = r.pop('_insns'), r.pop('_code')
        owner, template, slots = im.owner(rva)
        nm = im.best_name(rva)
        r['owner'] = owner
        r['template'] = template
        r['slots'] = sorted({k for _, k in slots})[:4]
        r['nslot_refs'] = len(slots)
        r['name'] = nm[0] if nm else None
        r['name_source'] = nm[1] if nm else None
        r['name_how'] = nm[3] if nm else None
        r['ghidra_name'] = name
        if r['size'] <= 64:
            r['describe'] = describe(insns, code, r)
        records.append(r)
        if progress and len(records) % 20000 == 0:
            print('  analysed %d functions (%.0f s)' % (len(records), time.time() - t0), file=sys.stderr)
    return records, errors


def target_label(im, rva, cache):
    if rva in cache:
        return cache[rva]
    label = None
    if rva in im.img.imports:
        label = '__imp_' + im.img.imports[rva][1]
    elif rva == 0:
        label = '__ImageBase'
    elif rva in im.vtables_raw:
        c = im.class_of_vtable.get(rva)
        label = 'vftable:' + (im.display.get(c[0], c[0]) if c else im.vtables_raw[rva][1])
    else:
        n = im.best_name(rva)
        if n:
            label = n[0]
        elif rva in im.index:
            owner, _, slots = im.owner(rva)
            if owner:
                label = '%s slot %d' % (owner, slots[0][1])
    cache[rva] = label
    return label


def cluster_rows(im, records):
    """One JSON-able dict per masked cluster with two or more members."""
    exact_size = collections.Counter(r['exact'] for r in records)
    shape_size = collections.Counter(r['shape'] for r in records)
    labels = {}
    for cid, members in partition(records, 'masked').items():
        if len(members) < 2:
            continue
        cols = columns(members)
        case = stamp_case(members)
        rows = []
        for m in members:
            rows.append({'rva': '0x%x' % m['rva'], 'size': m['size'], 'name': m['name'],
                         'name_source': m['name_source'], 'name_how': m['name_how'], 'owner': m['owner'],
                         'template': m['template'], 'slots': m['slots'], 'exact': m['exact'],
                         'targets': [['0x%x' % off, kind, '0x%x' % t, target_label(im, t, labels)]
                                     for off, kind, t in m['targets']],
                         'stampable': stampable(m, case, [target_label(im, t, labels) for _o, _k, t in m['targets']])})
        yield {'cluster': 'm:' + cid, 'members': len(members), 'size': members[0]['size'],
               'bytes': sum(m['size'] for m in members), 'exact_groups': len({m['exact'] for m in members}),
               'largest_exact_group': max(exact_size[m['exact']] for m in members),
               'shape': members[0]['shape'], 'shape_members': shape_size[members[0]['shape']],
               'case': case, 'eh': members[0]['eh'], 'flags': sorted(set().union(*[set(m['flags']) for m in members])),
               'columns': [['0x%x' % off, kind, varies] for off, kind, varies in cols],
               'named': sum(1 for m in members if m['name']),
               'named_ng': sum(1 for m in members if m['name_source'] == 'CommonLibSSE-NG'),
               'owned': sum(1 for m in members if m['owner']),
               'stampable': sum(1 for r in rows if r['stampable']),
               'describe': next((m.get('describe') for m in members if m.get('describe')), None),
               'member_list': rows}


def summary(records, errors, im_groups_count):
    by = {}
    for level in ('exact', 'masked', 'shape'):
        by[level] = level_summary(partition(records, level))
    flags = collections.Counter()
    for r in records:
        flags.update(r['flags'])
    return {'schema': imagemodel.SCHEMA, 'population': len(records), 'population_bytes': sum(r['size'] for r in records),
            'decode_errors': dict(errors), 'flags': dict(flags), 'levels': by,
            'eh_functions': sum(1 for r in records if r['eh']),
            'named': sum(1 for r in records if r['name']), 'owned': sum(1 for r in records if r['owner'])}


def print_summary(s, out=sys.stdout):
    print('population %d functions, %d bytes; decode errors %s; flags %s' % (
        s['population'], s['population_bytes'], s['decode_errors'], s['flags']), file=out)
    for level, v in s['levels'].items():
        print('%s: %d repeat an earlier member (%d bytes); singletons %d' % (
            level, v['repeats'], v['repeat_bytes'], v['singletons']), file=out)
        for b, row in v['buckets'].items():
            print('  members %-6s clusters %6d functions %6d bytes %8d' % (b, row['clusters'], row['functions'],
                                                                        row['bytes']), file=out)


def cmd_build(args):
    cfg = imagemodel.load_config(args.config)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    im = imagemodel.open_image(cfg, args.export or cfg['export'])
    groups = tuple(args.groups.split(',')) if args.groups else DEFAULT_GROUPS
    records, errors = analyse_population(im, groups)
    with open(out / 'functions.pkl', 'wb') as f:
        pickle.dump({'schema': imagemodel.SCHEMA, 'groups': groups, 'records': records}, f)
    exact_size = collections.Counter(r['exact'] for r in records)
    masked_size = collections.Counter(r['masked'] for r in records)
    shape_size = collections.Counter(r['shape'] for r in records)
    with open(out / 'function-clusters.tsv', 'w') as f:
        f.write('rva\tsize\tmasked\tmasked_members\texact\texact_members\tshape\tshape_members\teh\tname\towner\n')
        for r in records:
            f.write('0x%x\t%d\tm:%s\t%d\t%s\t%d\t%s\t%d\t%d\t%s\t%s\n' % (
                r['rva'], r['size'], r['masked'], masked_size[r['masked']], r['exact'], exact_size[r['exact']],
                r['shape'], shape_size[r['shape']], r['eh'], r['name'] or '', r['owner'] or ''))
    n = 0
    with open(out / 'clusters.jsonl', 'w') as f:
        for row in sorted(cluster_rows(im, records), key=lambda r: -r['bytes']):
            f.write(json.dumps(row) + '\n')
            n += 1
    s = summary(records, errors, None)
    s['masked_clusters_written'] = n
    (out / 'summary.json').write_text(json.dumps(s, indent=1) + '\n')
    print_summary(s)
    return 0


def load_clusters(path):
    out = {}
    for line in open(path):
        row = json.loads(line)
        out[row['cluster']] = row
    return out


def load_index(path):
    out = {}
    with open(path) as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            out[int(p[0], 16)] = p
    return out


def cmd_show(args):
    out = Path(args.out)
    idx = load_index(out / 'function-clusters.tsv')
    clusters = load_clusters(out / 'clusters.jsonl')
    for a in args.rva:
        rva = int(a, 16)
        row = idx.get(rva)
        if not row:
            print('%s: not in the analysed population' % a)
            continue
        c = clusters.get(row[2])
        print('%s size %s masked %s (%s members) exact %s members, shape %s members' % (
            a, row[1], row[2], row[3], row[5], row[7]))
        if c:
            print(json.dumps({k: v for k, v in c.items() if k != 'member_list'}))
            for m in c['member_list'][:args.limit]:
                print('  ', json.dumps(m))
    return 0


def read_exemplars(path):
    """{rva: (status, unit)} from a TSV of `rva status unit`, '#' comments allowed."""
    out = {}
    for line in open(path):
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        p = line.split()
        out[int(p[0], 16)] = (p[1], p[2] if len(p) > 2 else None)
    return out


EXEMPLAR_WEIGHT = {'accepted': 3.0, 'passing': 2.0}
# Internal-linkage copies cannot be compared under contract v2 and an unowned member has no
# plausible class to put the method on, so both count for less than members with an identity.
CASE_WEIGHT = {'class-methods': 1.0, 'template': 1.0, 'duplicate-helper': 0.5, 'unowned': 0.5}


def score(row, exemplar_status=None):
    """Bytes a solved exemplar would let the verifier check without a Drafter, weighted.

    (members - 1) * size is the code covered beyond the exemplar; named members count fully,
    members with only a class identity at a half, the rest at a quarter; duplicated helpers and
    unowned clusters at half weight (CASE_WEIGHT); an existing accepted or passing exemplar
    multiplies by 3 or 2, because the solve is already paid for.
    """
    m = row['members']
    named = row['named'] or 0
    owned_only = max(0, row['stampable'] - named)
    weight = (named + owned_only * 0.5 + (m - named - owned_only) * 0.25) / m
    w = EXEMPLAR_WEIGHT.get(exemplar_status, 1.0) * CASE_WEIGHT.get(row['case'], 0.5)
    return (m - 1) * row['size'] * weight * w


def choose_exemplar(row, exemplars):
    """The member to solve first: an existing accepted or passing one, else the smallest-RVA member
    with a CommonLibSSE-NG name from a declared identifier, else any named, else any owned."""
    for m in row['member_list']:
        if int(m['rva'], 16) in exemplars:
            return m, exemplars[int(m['rva'], 16)][0]
    for pred in (lambda m: m['name_source'] == 'CommonLibSSE-NG' and m['name_how'] == 'table',
                 lambda m: m['name_source'] == 'CommonLibSSE-NG', lambda m: m['name'], lambda m: m['owner']):
        for m in row['member_list']:
            if pred(m):
                return m, None
    return row['member_list'][0], None


MIDDLEWARE = ('std::', 'stdext::', 'Concurrency::', 'bnet', 'hk', 'Scaleform', 'GFx', 'GAS', 'type_info')


def is_middleware(row):
    """Most owned or named members are CRT/STL, Havok, Scaleform or Bethesda.net classes, which the
    decision table of docs/resource-guidelines.md puts out of scope."""
    names = [m['owner'] or m['name'] for m in row['member_list'] if m['owner'] or m['name']]
    if not names:
        return False
    return sum(1 for n in names if n.startswith(MIDDLEWARE)) * 2 > len(names)


def cmd_rank(args):
    out = Path(args.out)
    clusters = load_clusters(out / 'clusters.jsonl')
    exemplars = read_exemplars(args.exemplars) if args.exemplars else {}
    ranked = []
    for row in clusters.values():
        if args.skip_eh and row['eh']:
            continue
        if not args.with_middleware and is_middleware(row):
            continue
        ex, status = choose_exemplar(row, exemplars)
        ranked.append((score(row, status), row, ex, status))
    ranked.sort(key=lambda t: -t[0])
    result = []
    for s, row, ex, status in ranked[:args.top]:
        result.append({'score': round(s), 'cluster': row['cluster'], 'members': row['members'], 'size': row['size'],
                       'case': row['case'], 'named': row['named'], 'stampable': row['stampable'], 'eh': row['eh'],
                       'describe': row['describe'], 'exemplar': ex['rva'], 'exemplar_name': ex['name'] or ex['owner'],
                       'exemplar_status': status})
    text = json.dumps(result, indent=1)
    if args.write:
        Path(args.write).write_text(text + '\n')
    print(text)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--config', default=str(DEFAULT_CONFIG))
    b.add_argument('--export', help='Ghidra export listing (F/V lines); default: the config key "export"')
    b.add_argument('--groups', help='comma-separated POGO groups (default .text$mn)')
    b.add_argument('--out', default=str(DEFAULT_OUT))
    s = sub.add_parser('show')
    s.add_argument('rva', nargs='+')
    s.add_argument('--out', default=str(DEFAULT_OUT))
    s.add_argument('--limit', type=int, default=12)
    r = sub.add_parser('rank')
    r.add_argument('--out', default=str(DEFAULT_OUT))
    r.add_argument('--exemplars')
    r.add_argument('--top', type=int, default=30)
    r.add_argument('--skip-eh', action='store_true')
    r.add_argument('--with-middleware', action='store_true')
    r.add_argument('--write')
    args = ap.parse_args(argv)
    return {'build': cmd_build, 'show': cmd_show, 'rank': cmd_rank}[args.cmd](args)


if __name__ == '__main__':
    raise SystemExit(main())
