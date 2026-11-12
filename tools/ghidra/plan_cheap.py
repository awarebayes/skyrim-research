"""Low-cost batch planning: many small functions per Drafter, grouped into shared-header families.

    python3 tools/ghidra/export_pack.py plan --order cheap --label fifth-batch --total 232 \
        --task-prefix batch5- --parked <census.json> --evidence findings/fifth-batch-selection.md

A Drafter run has a fixed start-up cost (card, cookbook, class material) and a per-function cost;
small functions without exception data passed in one or two attempts in the fourth batch. So this
planner picks functions expected to pass cheaply and packs many of them into one task:

- **small** tasks: 15 to 25 functions of at most 64 bytes from classes of one family (a common base
  in the image's RTTI), one translation unit per class, all units in one task directory;
- **normal** tasks: one class with 6 to 10 functions, most of them 64 to 512 bytes.

Eligibility adds to `export_pack.table_eligibility`: no exception-handling data, no thread-local
read (scanned in the image bytes), not in the two parked families of the census (callee-saved
saves that skip the first home slot; an EH state store without a handler), a class whose skeleton
is verified (passes the per-class checks and has a size from its deleting destructor), and no
class that already has a unit or an open task (editing an accepted unit stales its records).
Preference: an FNV counterpart, a class in the FNV inline-helper catalogue, small size, a base
class whose header already exists, fan-in; one function per L1 cluster.

Pure functions here; `export_pack.cmd_plan_cheap` reads the tables and writes the plan files.
"""
from collections import Counter, defaultdict
import re

# mov r64, gs:[0x58] (the TLS array pointer of the TEB), any destination register: the start of
# every thread-local read the compiler emits for __declspec(thread) data in this image.
TLS_READ = re.compile(rb'\x65[\x48\x4c]\x8b[\x04\x0c\x14\x1c\x24\x2c\x34\x3c]\x25\x58\x00\x00\x00')

DEFAULTS = {'total': 232, 'max_function_bytes': 512, 'small_bytes': 64, 'small_task_min': 15,
            'small_task_max': 25, 'small_task_floor': 10, 'small_per_class': 8, 'normal_min': 6,
            'normal_max': 10, 'normal_functions': 60, 'task_prefix': 'batch5-', 'small_attempts_per_function': 2,
            'small_attempts_floor': 3, 'normal_attempts_per_function': 3, 'normal_attempts_extra': 4}


def tls_rvas(read, rows):
    """RVAs of rows whose bytes hold a thread-local read; `read(rva, size)` returns the bytes."""
    out = set()
    for r in rows:
        try:
            blob = read(r['rva'], r['size'] or 0)
        except Exception:  # noqa: BLE001 - an unreadable range is reported as not scanned, not as clean
            out.add(r['rva'])
            continue
        if TLS_READ.search(blob):
            out.add(r['rva'])
    return out


def verified_skeleton(c):
    """A class whose generated skeleton is checked: a community header passes C1 to C3 for it and
    its size comes from the deleting destructor (C4)."""
    return bool(c and c.get('passes') and c.get('size'))


def extra_reason(row, classes, opts):
    """Why a row that `table_eligibility` admits is still left out of a cheap batch, or None."""
    eh = row.get('eh') or {}
    if eh.get('handler') or eh.get('handler_kind'):
        return 'exception-handling data'
    if row['rva'] in opts.get('parked', ()):
        return 'parked family (census)'
    if row['rva'] in opts.get('tls', ()):
        return 'thread-local reference'
    cls = row['owner']['class']
    if cls in opts.get('skip_classes', ()):
        return 'class has a unit or an open task'
    if not verified_skeleton(classes.get(cls)):
        return 'class has no verified skeleton'
    return None


def score(row, classes, opts):
    """Higher is cheaper to draft: an FNV counterpart, catalogue helpers, small size, existing base
    headers, then fan-in."""
    cls = row['owner']['class']
    s = 0.0
    if row['rva'] in opts.get('fnv_rvas', ()):
        s += 3 + (1 if row['rva'] in opts.get('fnv_o2_rvas', ()) else 0)
    if cls in opts.get('catalogue', ()):
        s += 1
    size = row['size'] or 0
    s += 2 if size <= opts['small_bytes'] else (1 if size <= 128 else 0)
    if any(a in opts.get('headers', ()) for a in classes[cls].get('ancestors') or ()):
        s += 1
    return s + min(row.get('callers') or 0, 20) / 10


def family_of(classes, small_counts, cls, need):
    """The nearest of the class and its ancestors whose subtree holds at least `need` selected small
    functions; the root ancestor when none does."""
    chain = [cls] + list(classes[cls].get('ancestors') or [])
    for c in chain:
        if small_counts.get(c, 0) >= need:
            return c
    return chain[-1]


def chunk(units, lo, hi):
    """Split an ordered list of (class, functions) into consecutive groups of at most `hi` functions,
    never splitting a class; a group under `lo` joins the previous one when that stays within `hi`."""
    groups, cur, n = [], [], 0
    for cls, fs in units:
        if cur and n + len(fs) > hi:
            groups.append(cur)
            cur, n = [], 0
        cur.append((cls, fs))
        n += len(fs)
    if cur:
        if groups and n < lo and sum(len(f) for _, f in groups[-1]) + n <= hi:
            groups[-1] += cur
        else:
            groups.append(cur)
    return groups


def plan(rows, classes, claimed, opts, eligibility):
    """(tasks, stats). `eligibility(row, classes, claimed, max_bytes)` is export_pack's check.

    A task is {'kind', 'id', 'family', 'units': [{'class', 'functions': [row, ...]}], 'score'}."""
    o = dict(DEFAULTS, **opts)
    elig, rejected = [], Counter()
    for r in rows:
        why = eligibility(r, classes, claimed, o['max_function_bytes']) or extra_reason(r, classes, o)
        if why:
            rejected[why] += 1
        else:
            elig.append(r)
    for r in elig:
        r['_score'] = score(r, classes, o)
    # One function per L1 cluster: the rest of a cluster is the stamping lane's, not a Drafter's.
    seen, picked = set(), []
    for r in sorted(elig, key=lambda r: (-r['_score'], r['size'] or 0, r['rva'])):
        if r['l1'] in seen:
            continue
        seen.add(r['l1'])
        picked.append(r)
    by_class = defaultdict(list)
    for r in picked:
        by_class[r['owner']['class']].append(r)
    normal, small = {}, {}
    for cls, fs in by_class.items():
        big = [f for f in fs if (f['size'] or 0) > o['small_bytes']]
        if len(fs) >= o['normal_min'] and 2 * len(big) >= len(fs):
            # The 64 to 512 byte functions are what a normal task is for; the class's small ones fill
            # the rest, since one class has one unit and they could not go to another task.
            key = lambda r: (-r['_score'], r['rva'])  # noqa: E731
            tiny = [f for f in fs if f not in big]
            normal[cls] = (sorted(big, key=key) + sorted(tiny, key=key))[:o['normal_max']]
        else:
            tiny = sorted((f for f in fs if (f['size'] or 0) <= o['small_bytes']), key=lambda r: (-r['_score'], r['rva']))
            if tiny:
                small[cls] = tiny[:o['small_per_class']]
    counts = Counter()
    for cls, fs in small.items():
        for c in [cls] + list(classes[cls].get('ancestors') or []):
            counts[c] += len(fs)
    families = defaultdict(list)
    for cls in small:
        families[family_of(classes, counts, cls, o['small_task_min'])].append(cls)
    tasks = []
    for fam, members in families.items():
        # Siblings next to each other, so a split keeps subfamilies (and their shared bases) together.
        members.sort(key=lambda c: (list(reversed(classes[c].get('ancestors') or [])), c))
        for group in chunk([(c, small[c]) for c in members], o['small_task_min'], o['small_task_max']):
            n = sum(len(fs) for _, fs in group)
            if n < o['small_task_floor']:
                rejected['small family too small for a task'] += n
                continue
            fs_all = [f for _, fs in group for f in fs]
            tasks.append({'kind': 'small', 'family': fam,
                          'units': [{'class': c, 'functions': sorted(fs, key=lambda r: (r['size'] or 0, r['rva']))}
                                    for c, fs in group],
                          'score': sum(f['_score'] for f in fs_all) / len(fs_all)})
    for cls, fs in normal.items():
        tasks.append({'kind': 'normal', 'family': cls,
                      'units': [{'class': cls, 'functions': sorted(fs, key=lambda r: (r['size'] or 0, r['rva']))}],
                      'score': sum(f['_score'] for f in fs) / len(fs)})
    tasks.sort(key=lambda t: (-t['score'], t['kind'], t['family']))
    # Normal tasks get a share of the batch first: ranked purely by score, the small families would
    # always win, and the 64 to 512 byte band would never be measured.
    chosen, total, quota = [], 0, o.get('normal_functions', o['total'] // 4)
    for kind, cap in (('normal', quota), ('small', o['total'])):
        for t in tasks:
            n = sum(len(u['functions']) for u in t['units'])
            if t['kind'] != kind or total + n > o['total'] or \
                    (kind == 'normal' and sum(len(u['functions']) for c in chosen for u in c['units']) + n > cap):
                continue
            chosen.append(t)
            total += n
    chosen.sort(key=lambda t: (-t['score'], t['kind'], t['family']))
    s_i = n_i = 0
    for t in chosen:
        if t['kind'] == 'small':
            s_i += 1
            t['id'] = f'{o["task_prefix"]}s{s_i:02d}-{slug(t["family"])}'[:48]
            for u in t['units']:
                u['task_id'] = f'{t["id"][:34]}-{slug(u["class"])}'[:56].rstrip('-.')
                u['budget'] = max(o['small_attempts_floor'], o['small_attempts_per_function'] * len(u['functions']))
        else:
            n_i += 1
            t['id'] = f'{o["task_prefix"]}{slug(t["family"])}'[:56]
            u = t['units'][0]
            u['task_id'] = t['id']
            u['budget'] = o['normal_attempts_per_function'] * len(u['functions']) + o['normal_attempts_extra']
        t['budget'] = sum(u['budget'] for u in t['units'])
    stats = {'eligible': len(elig), 'one_per_cluster': len(picked), 'rejections': dict(rejected.most_common()),
             'tasks': dict(Counter(t['kind'] for t in chosen)), 'functions': total}
    return chosen, stats


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'x'


def composition(tasks, classes, fnv_rvas, area_for):
    """Counts for the public finding: size bands, areas, FNV counterparts, cluster members."""
    fs = [(u['class'], f) for t in tasks for u in t['units'] for f in u['functions']]
    bands = Counter()
    for _, f in fs:
        n = f['size'] or 0
        bands['<=32' if n <= 32 else '33-64' if n <= 64 else '65-128' if n <= 128 else '129-256' if n <= 256
              else '257-512'] += 1
    return {'functions': len(fs), 'bytes': sum(f['size'] or 0 for _, f in fs),
            'classes': len({c for c, _ in fs}), 'size_bands': dict(bands),
            'areas': dict(Counter(area_for(c) for c, _ in fs)),
            'fnv_counterpart': sum(1 for _, f in fs if f['rva'] in fnv_rvas),
            'cluster_members': sum(1 for _, f in fs if (f.get('cluster_size') or 1) > 1),
            'tasks': dict(Counter(t['kind'] for t in tasks))}
