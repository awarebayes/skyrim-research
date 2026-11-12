"""Census of instruction runs that recur inside many functions: inlined helpers (P2 of the
ideas document).

Each instruction becomes a token: its register-abstracted encoding (`tools/analysis/x64.py` key:
opcode, operand size, addressing form, displacements other than stack ones, immediates) plus the
identity of what it references: the target RVA of a call, jump or data operand (`--targets mask`
drops it), or for a branch inside the function the distance in instructions. Prologue
instructions (inside the unwind prolog), epilogue restores, pushes, pops, returns, padding and
nops are separators. A window is K consecutive tokens with no separator: every window of
`--k-long` tokens (default 6), and windows of `--k-short` tokens (default 4) that hold a
reference, so a short accessor that reads a global still counts. Windows found in at least
`--min-hosts` functions are frequent; overlapping frequent windows inside one function merge into
a maximal run, and identical runs are one recurring body. A body also seen twice in one function
is a self-repeat (a helper called twice). A small function (`--twin-max` instructions or fewer)
whose own tokens contain the body, with the body covering at least half of it, is the body's
out-of-line twin: a compiled reference with an address, often a community name.

Only one representative of each masked cluster is scanned (the copies have the same code);
every other member inherits its representative's bodies at the same offsets.

Usage (repository root; outputs are game-derived and stay under `.local/`):

    python3 tools/analysis/inline_census.py build [--config ...] [--out .local/analysis/census]
    python3 tools/analysis/inline_census.py show 0x<rva> [...]          # bodies inside these functions
    python3 tools/analysis/inline_census.py export --dest <dir> 0x<rva> [...]   # per-function files

`build` writes `bodies.jsonl` (one recurring body per line), `functions.jsonl` (per scanned
function: its bodies with offsets) and `summary.json` (counts only), and prints the summary.
`export` writes `<dest>/<rva>/inlined-bodies.json` in the format of `PER_FUNCTION_FORMAT`.
"""
import argparse
import array
import collections
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import x64  # noqa: E402

DEFAULT_CONFIG = REPO / '.local/config/analysis.json'
DEFAULT_OUT = REPO / '.local/analysis/census'
PER_FUNCTION_SCHEMA = 1
PER_FUNCTION_FORMAT = """inlined-bodies.json, schema 1:
{"schema": 1, "build_id": "...", "rva": "0x...", "generator": "tools/analysis/inline_census.py",
 "census": {"min_hosts": N, "k_long": 6, "k_short": 4, "targets": "keep"},
 "via_representative": "0x..." or null,
 "bodies": [{"body": "b:<id>", "instructions": n, "hosts": n, "self_repeats": n,
             "places": [[start offset, end offset], ...],
             "twin": {"rva": "0x...", "size": n, "name": "..." or null, "name_source": "..." or null} or null,
             "references": [["call" | "data", "0x<target rva>", "<name or null>"], ...],
             "guess": "<helper identity in words, from the twin's or the references' names>" or null}],
 "self_repeats": [{"places": [[start, end], [start, end], ...]}, ...]}
`self_repeats` are code runs that occur twice or more inside this function only (a helper called
twice, branch sense ignored); they have no host count or twin.
Offsets are byte offsets from the function start; `places` lists every occurrence in this function."""

SEP = 0
JCC_TOKEN = 0x4A4343
PUSH_POP = frozenset(range(0x50, 0x60))
RSP_ADJUST = (b'\x48\x83\xec', b'\x48\x83\xc4', b'\x48\x81\xec', b'\x48\x81\xc4')


def tokenize(insns, code, rva, size, prolog_size, image_base=0, mask_targets=False, relaxed=None, spec=None):
    """(tokens, byte offsets, anchored flags) for one function's decoded instructions.

    Tokens are non-zero ints; SEP marks a separator. `anchored` is 1 where the token names a call
    or data target (so a short window holding it is specific to one helper). When `relaxed` and
    `spec` are lists of length len(insns), they receive tokens with branch conditions dropped and
    a flag for instructions specific enough to anchor a self-repeat (a reference, or a memory
    operand with a non-stack displacement).
    """
    n = len(insns)
    toks = [SEP] * n
    anch = bytearray(n)
    offs = array.array('I', (off for off, _ in insns))
    for i, (off, ins) in enumerate(insns):
        f = ins.flow
        if f in (x64.RET, x64.INT3, x64.NOP) or off < prolog_size:
            continue
        if len(ins.opcode) == 1 and ins.opcode[0] in PUSH_POP:
            continue
        if bytes(code[off:off + 3]) in RSP_ADJUST:
            continue
        ref = None
        if ins.rel is not None:
            t = ins.target - image_base
            if rva <= t < rva + size and f != x64.CALL:
                # Two inlined copies of one helper leave to different places, so a branch inside
                # the function keeps its condition (in the key) but not its distance.
                ref = (1,)
            else:
                ref = (2, -1 if mask_targets else t)
                anch[i] = 1
        elif ins.rip is not None:
            t = ins.rip_target - image_base
            ref = (3, -1 if mask_targets else t)
            anch[i] = 1
        # Only ints go into hashed tuples, so tokens and body ids are the same in every run.
        h = hash((int.from_bytes(ins.key, 'little'), len(ins.key), ref)) & 0x7FFFFFFFFFFFFFFF
        toks[i] = h or 1
        if relaxed is not None:
            # Inlined twice, a helper's test can come out with the opposite branch sense.
            relaxed[i] = (JCC_TOKEN if f == x64.JCC else h) or 1
            spec[i] = 1 if anch[i] or (ins.disp is not None and ins.base not in (4, None)) else 0
    # Epilogue restores before each return are frame bookkeeping, not part of any body.
    for i, (off, ins) in enumerate(insns):
        if ins.flow == x64.RET or (ins.flow == x64.JMP and ins.rel and toks[i] and anch[i]):
            j = i - 1
            while j >= 0:
                o, p = insns[j]
                if (len(p.opcode) == 1 and p.opcode[0] in PUSH_POP) or bytes(code[o:o + 3]) in RSP_ADJUST \
                        or (p.opcode == (0x8B,) and p.base == 4):
                    toks[j] = SEP
                    if relaxed is not None:
                        relaxed[j] = SEP
                    j -= 1
                else:
                    break
    return toks, offs, anch


def windows(toks, anch, k_long, k_short):
    """[(start, length, hash)] of eligible windows."""
    out = []
    n = len(toks)
    run = 0
    for i in range(n):
        run = run + 1 if toks[i] else 0
        if run >= k_long:
            s = i - k_long + 1
            out.append((s, k_long, hash(tuple(toks[s:i + 1]))))
        if k_short and run >= k_short:
            s = i - k_short + 1
            if any(anch[s:i + 1]):
                out.append((s, k_short, hash((-1,) + tuple(toks[s:i + 1]))))
    return out


def self_repeats(relaxed, spec, k=3):
    """[[(start, end), ...]] groups of instruction ranges that repeat inside one function.

    Windows of k relaxed tokens holding a specific instruction that occur at two or more
    non-overlapping places; overlapping repeated windows merge into runs, grouped by content.
    """
    pos = collections.defaultdict(list)
    n = len(relaxed)
    for s in range(0, n - k + 1):
        w = relaxed[s:s + k]
        if SEP in w or not any(spec[s:s + k]):
            continue
        pos[tuple(w)].append(s)
    marks = []
    for w, starts in pos.items():
        keep = []
        for s in starts:
            if not keep or s >= keep[-1] + k:
                keep.append(s)
        if len(keep) >= 2:
            marks.extend((s, s + k) for s in keep)
    marks.sort()
    runs = []
    for s, e in marks:
        if runs and s < runs[-1][1]:
            runs[-1][1] = max(runs[-1][1], e)
        else:
            runs.append([s, e])
    groups = collections.defaultdict(list)
    for s, e in runs:
        groups[tuple(relaxed[s:e])].append((s, e))
    return [g for g in groups.values() if len(g) >= 2]


class Census:
    """Window counts over host functions, then maximal runs (bodies) per host."""

    def __init__(self, k_long=6, k_short=4, min_hosts=2):
        self.k_long, self.k_short, self.min_hosts = k_long, k_short, min_hosts
        self.counts = {}       # window hash -> hosts * 2**24 + last host id
        self.hosts = {}

    def add(self, host, toks, anch):
        self.hosts[host] = (toks, anch)
        for _s, _k, h in windows(toks, anch, self.k_long, self.k_short):
            v = self.counts.get(h)
            if v is None:
                self.counts[h] = (1 << 24) | host
            elif (v & 0xFFFFFF) != host:
                self.counts[h] = (((v >> 24) + 1) << 24) | host

    def window_hosts(self, h):
        v = self.counts.get(h)
        return 0 if v is None else v >> 24

    def runs(self, host):
        """[(start, end)] instruction index ranges of maximal runs of frequent windows in a host."""
        toks, anch = self.hosts[host]
        cover = []
        wins = windows(toks, anch, self.k_long, self.k_short)
        local = collections.Counter(h for _s, _k, h in wins)
        for s, k, h in wins:
            # A window seen twice in one function is a helper called twice there.
            if self.window_hosts(h) >= self.min_hosts or local[h] >= 2:
                cover.append((s, s + k))
        cover.sort()
        out = []
        for s, e in cover:
            if out and s < out[-1][1]:
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return [tuple(r) for r in out]


def body_key(toks, s, e):
    return hash(tuple(toks[s:e])) & 0x7FFFFFFFFFFFFFFF


def contains(seq, sub):
    """Index of `sub` as a contiguous part of `seq`, or -1."""
    n, m = len(seq), len(sub)
    if m == 0 or m > n:
        return -1
    first = sub[0]
    for i in range(n - m + 1):
        if seq[i] == first and seq[i:i + m] == sub:
            return i
    return -1


def find_bodies(census, rep_meta):
    """{body key: record} and {host: [(body key, start, end)]} from the census runs.

    rep_meta[host] = (rva, byte offsets). Runs that occur in fewer than min_hosts hosts are
    dropped: they are unions of windows shared with different functions, not one body.
    """
    per_host = {}
    occ = collections.defaultdict(list)
    for host in census.hosts:
        toks, _ = census.hosts[host]
        found = []
        for s, e in census.runs(host):
            key = body_key(toks, s, e)
            found.append((key, s, e))
            occ[key].append((host, s, e))
        per_host[host] = found
    bodies = {}
    for key, places in occ.items():
        hosts = {h for h, _, _ in places}
        per = collections.Counter(h for h, _, _ in places)
        if len(hosts) < census.min_hosts and max(per.values()) < 2:
            continue
        h0, s0, e0 = places[0]
        bodies[key] = {'key': key, 'instructions': e0 - s0, 'hosts': len(hosts),
                       'self_repeats': sum(1 for c in per.values() if c > 1),
                       'example': (h0, s0, e0), 'places': places}
    for host in per_host:
        per_host[host] = [t for t in per_host[host] if t[0] in bodies]
    return bodies, per_host


def find_twins(bodies, census, small):
    """Attach the smallest out-of-line twin: small[host] = token list of a small function."""
    index = collections.defaultdict(set)
    k = census.k_short or census.k_long
    for host, seq in small.items():
        for i in range(len(seq) - k + 1):
            index[tuple(seq[i:i + k])].add(host)
    for key, b in bodies.items():
        h0, s0, e0 = b['example']
        toks = census.hosts[h0][0]
        sub = toks[s0:e0]
        cands = index.get(tuple(sub[:k]), ())
        best = None
        for c in cands:
            seq = small[c]
            if contains(seq, sub) >= 0 and 2 * len(sub) >= len(seq):
                if best is None or len(small[c]) < len(small[best]):
                    best = c
        b['twin'] = best


# --- whole-image driver ------------------------------------------------------------------------

def scan(im, groups, args):
    import imagemodel
    reps = {}
    members_of = collections.defaultdict(list)
    meta = {}
    small = {}
    census = Census(args.k_long, args.k_short, args.min_hosts)
    self_found = {}
    t0 = time.time()
    host = 0
    for i, (rva, size, name) in enumerate(im.funcs):
        if im.group[i] not in groups or imagemodel.is_funclet_name(name) or name.startswith('thunk_'):
            continue
        r = im.analyse(i)
        if 'error' in r:
            continue
        cid = r['masked']
        members_of[cid].append(rva)
        if cid in reps:
            continue
        insns, code = r['_insns'], r['_code']
        prolog = 0
        pd = im.img.pdata_at.get(rva)
        if pd:
            try:
                prolog = im.img.read(pd[1], 2)[1]
            except Exception:
                prolog = 0
        relaxed, spec = [SEP] * len(insns), bytearray(len(insns))
        toks, offs, anch = tokenize(insns, code, rva, r['size'], prolog, im.image_base, args.targets == 'mask',
                                    relaxed, spec)
        reps_self = self_repeats(relaxed, spec, args.k_self)
        if reps_self:
            self_found[host + 1] = [[(offs[s], offs[e] if e < len(offs) else r['size']) for s, e in g] for g in reps_self]
        host += 1
        reps[cid] = host
        meta[host] = (rva, offs, r['size'], i)
        census.add(host, toks, anch)
        nz = [t for t in toks if t]
        if len(nz) <= args.twin_max:
            small[host] = nz
        if host % 20000 == 0:
            print('  scanned %d representatives (%.0f s)' % (host, time.time() - t0), file=sys.stderr)
    return census, reps, members_of, meta, small, self_found


def reference_list(meta, host, s, e, im, labels):
    rva, offs, size, i = meta[host]
    # Decoded instructions are not kept for every host (memory); decode the example again.
    insns = im.analyse(i)['_insns']
    out = []
    for off, ins in insns[s:e]:
        if ins.rel is not None and ins.flow == x64.CALL:
            t = ins.target - im.image_base
            out.append(['call', '0x%x' % t, label(im, t, labels)])
        elif ins.rel is not None and not (rva <= ins.target - im.image_base < rva + size):
            t = ins.target - im.image_base
            out.append(['jump', '0x%x' % t, label(im, t, labels)])
        elif ins.rip is not None:
            t = ins.rip_target - im.image_base
            out.append(['data', '0x%x' % t, label(im, t, labels)])
    return out


def label(im, rva, cache):
    if rva not in cache:
        n = im.best_name(rva)
        if n:
            cache[rva] = n[0]
        elif rva in im.img.imports:
            cache[rva] = '__imp_' + im.img.imports[rva][1]
        else:
            owner, _, slots = im.owner(rva) if rva in im.index else (None, False, [])
            cache[rva] = ('%s slot %d' % (owner, slots[0][1])) if owner else None
    return cache[rva]


def guess(b, twin_name, refs):
    if twin_name:
        return 'inlined copy of %s' % twin_name
    named = [r[2] for r in refs if r[2]]
    if named:
        return 'inlined code around %s' % ', '.join(sorted(set(named))[:3])
    return None


def cmd_build(args):
    import imagemodel
    cfg = imagemodel.load_config(args.config)
    im = imagemodel.open_image(cfg, cfg['export'])
    groups = tuple(args.groups.split(',')) if args.groups else ('.text$mn', '.text$mn$00')
    census, reps, members_of, meta, small, self_found = scan(im, groups, args)
    bodies, per_host = find_bodies(census, meta)
    find_twins(bodies, census, small)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    labels = {}
    rows = {}
    for key, b in bodies.items():
        h0, s0, e0 = b['example']
        refs = reference_list(meta, h0, s0, e0, im, labels)
        twin = None
        if b['twin'] is not None:
            trva, _, tsize, _ = meta[b['twin']]
            tn = im.best_name(trva)
            twin = {'rva': '0x%x' % trva, 'size': tsize, 'name': tn[0] if tn else None,
                    'name_source': tn[1] if tn else None}
        rows[key] = {'body': 'b:%016x' % key, 'instructions': b['instructions'], 'hosts': b['hosts'],
                     'self_repeats': b['self_repeats'], 'twin': twin, 'references': refs,
                     'guess': guess(b, twin and twin['name'], refs),
                     'host_rvas': sorted({'0x%x' % meta[h][0] for h, _, _ in b['places']})[:args.max_hosts_listed]}
    with open(out / 'bodies.jsonl', 'w') as f:
        for row in sorted(rows.values(), key=lambda r: (-r['hosts'], -r['instructions'])):
            f.write(json.dumps(row) + '\n')
    rep_of = {}
    for cid, rvas in members_of.items():
        h = reps[cid]
        for rva in rvas:
            rep_of[rva] = h
    with open(out / 'functions.jsonl', 'w') as f:
        for rva in sorted(rep_of):
            h = rep_of[rva]
            found = per_host.get(h) or []
            local = self_found.get(h) or []
            if not found and not local:
                continue
            offs, size = meta[h][1], meta[h][2]
            items = collections.defaultdict(list)
            for key, s, e in found:
                end = offs[e] if e < len(offs) else size
                items[key].append([offs[s], end])
            f.write(json.dumps({'rva': '0x%x' % rva, 'via_representative': None if meta[h][0] == rva else '0x%x' % meta[h][0],
                                'bodies': [[rows[k]['body'], p] for k, p in items.items()],
                                'self_repeats': [[list(p) for p in g] for g in local]}) + '\n')
    s = summarise(bodies, per_host, meta, rep_of, census)
    s['functions_with_self_repeats'] = len(self_found)
    s['self_repeat_groups'] = sum(len(v) for v in self_found.values())
    s['parameters'] = {'k_long': args.k_long, 'k_short': args.k_short, 'k_self': args.k_self, 'min_hosts': args.min_hosts,
                       'targets': args.targets, 'twin_max': args.twin_max}
    (out / 'summary.json').write_text(json.dumps(s, indent=1) + '\n')
    print(json.dumps(s, indent=1))
    return 0


def summarise(bodies, per_host, meta, rep_of, census):
    thresholds = (2, 5, 20, 100)
    by = {}
    for t in thresholds:
        sel = [b for b in bodies.values() if b['hosts'] >= t]
        by[str(t)] = {'bodies': len(sel), 'with_twin': sum(1 for b in sel if b.get('twin') is not None),
                      'self_repeating': sum(1 for b in sel if b['self_repeats'])}
    frequent_windows = {str(t): sum(1 for v in census.counts.values() if (v >> 24) >= t) for t in thresholds}
    large = [h for h in meta if meta[h][2] > 512]
    hosting = [h for h in large if any(bodies[k]['hosts'] >= 20 for k, _, _ in per_host.get(h, []))]
    covered = 0
    total = 0
    for h in large:
        total += len(meta[h][1])
        marks = set()
        for k, s, e in per_host.get(h, []):
            if bodies[k]['hosts'] >= 20:
                marks.update(range(s, e))
        covered += len(marks)
    return {'representatives': len(meta), 'functions': len(rep_of), 'windows_distinct': len(census.counts),
            'windows_by_min_hosts': frequent_windows, 'bodies_by_min_hosts': by,
            'large_representatives': len(large), 'large_with_a_body_of_20_hosts': len(hosting),
            'large_instructions_in_such_bodies': covered, 'large_instructions': total}


def load_functions(out):
    idx = {}
    for line in open(Path(out) / 'functions.jsonl'):
        row = json.loads(line)
        idx[int(row['rva'], 16)] = row
    return idx


def load_bodies(out):
    return {json.loads(l)['body']: json.loads(l) for l in open(Path(out) / 'bodies.jsonl')}


def per_function_record(row, bodies, build_id, params):
    out = []
    for bid, places in row['bodies']:
        b = bodies[bid]
        out.append({'body': bid, 'instructions': b['instructions'], 'hosts': b['hosts'],
                    'self_repeats': b['self_repeats'], 'places': places, 'twin': b['twin'],
                    'references': b['references'], 'guess': b['guess']})
    out.sort(key=lambda b: b['places'][0][0])
    return {'schema': PER_FUNCTION_SCHEMA, 'build_id': build_id, 'rva': row['rva'],
            'generator': 'tools/analysis/inline_census.py', 'census': params,
            'via_representative': row['via_representative'], 'bodies': out,
            'self_repeats': [{'places': g} for g in row.get('self_repeats', [])]}


def cmd_show(args):
    idx = load_functions(args.out)
    bodies = load_bodies(args.out)
    params = json.loads((Path(args.out) / 'summary.json').read_text()).get('parameters')
    for a in args.rva:
        row = idx.get(int(a, 16))
        if not row:
            print('%s: no recurring bodies' % a)
            continue
        rec = per_function_record(row, bodies, 'sse-steam-1-7-104', params)
        print(json.dumps(rec, indent=1))
    return 0


def cmd_export(args):
    idx = load_functions(args.out)
    bodies = load_bodies(args.out)
    params = json.loads((Path(args.out) / 'summary.json').read_text()).get('parameters')
    dest = Path(args.dest)
    n = 0
    for a in args.rva:
        row = idx.get(int(a, 16))
        if not row:
            continue
        d = dest / ('0x%x' % int(a, 16))
        d.mkdir(parents=True, exist_ok=True)
        (d / 'inlined-bodies.json').write_text(json.dumps(per_function_record(row, bodies, 'sse-steam-1-7-104', params),
                                                         indent=1) + '\n')
        n += 1
    print('wrote %d files' % n)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--config', default=str(DEFAULT_CONFIG))
    b.add_argument('--groups')
    b.add_argument('--out', default=str(DEFAULT_OUT))
    b.add_argument('--k-long', type=int, default=6)
    b.add_argument('--k-short', type=int, default=4)
    b.add_argument('--k-self', type=int, default=3)
    b.add_argument('--min-hosts', type=int, default=2)
    b.add_argument('--twin-max', type=int, default=40)
    b.add_argument('--targets', choices=['keep', 'mask'], default='keep')
    b.add_argument('--max-hosts-listed', type=int, default=50)
    s = sub.add_parser('show')
    s.add_argument('rva', nargs='+')
    s.add_argument('--out', default=str(DEFAULT_OUT))
    e = sub.add_parser('export')
    e.add_argument('rva', nargs='+')
    e.add_argument('--dest', required=True)
    e.add_argument('--out', default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)
    return {'build': cmd_build, 'show': cmd_show, 'export': cmd_export}[args.cmd](args)


if __name__ == '__main__':
    raise SystemExit(main())
