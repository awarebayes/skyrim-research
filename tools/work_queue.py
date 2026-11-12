#!/usr/bin/env python3
"""A work queue of prepared Drafter units that several sessions can drain at once.

    python3 tools/work_queue.py next --worker <label> [--profile cheap|full]  # claim the next unit, or EMPTY
    python3 tools/work_queue.py done <unit dir> --result '<json line>' [--result ...]
    python3 tools/work_queue.py release <unit dir> [--worker <label>]   # give back a claim you will not work
    python3 tools/work_queue.py status                      # open, claimed, stale and done units
    python3 tools/work_queue.py stats                       # pass rate and attempts per worker label and model
    python3 tools/work_queue.py add <unit or group dir>...  # append units (with skeleton and sheets) to the queue

The queue lives in `.local/queue/small/` (or `--queue-dir`, or $SKYRIM_QUEUE_DIR):

- `queue.tsv`: one line per unit, tab-separated: unit task dir, source paths (comma-separated),
  functions (comma-separated RVAs), attempt budget. Lines starting with `#` are comments.
- `claims/<unit>.lock`: created with O_EXCL, so of two sessions asking at once exactly one gets a
  unit. It holds the worker label and the claim time. A claim older than STALE_SECONDS with no
  result is taken over (the session that held it is assumed dead): the stale lock is renamed away
  first, and a rename succeeds for one caller only, so a takeover is atomic too.
- `done/<unit>.json` marks a unit finished; `results.jsonl` gets every result line, stamped with
  the worker label, the profile, the unit, the claim time and the time, so pass rates and wall time
  can be compared per model and profile afterwards (tools/friction.py).
- `releases.jsonl` lists claims given back with `release` (a session that asked `next` once too
  often), so the friction report can count them.
- On a claim, near-miss files left in `<unit dir>/near-miss/` by an earlier session are moved to
  `near-miss/earlier-<time>/`: they were written against an older unit source and confused later
  sessions when left beside the new run's files. They stay readable there.

A worker label names model and effort and ends in a session number (`luna56-medium-1`,
`haiku-1`); `stats` groups by the label and by the label without its trailing `-<n>`.

Not named queue.py: tools/ is on sys.path for many scripts and tests, and a tools/queue.py would
shadow the standard library module that concurrent.futures imports.
"""
import argparse
from collections import defaultdict
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

REPO = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO / '.local/queue/small'
# A session that has not reported within this time is treated as dead. Small units take a few
# minutes per attempt, so a live session holding one unit this long is unlikely.
STALE_SECONDS = 90 * 60
LABEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}')


class QueueError(Exception):
    pass


def queue_dir(arg=None):
    return Path(arg or os.environ.get('SKYRIM_QUEUE_DIR') or DEFAULT_DIR)


def read_queue(qdir):
    """[{'dir', 'sources', 'functions', 'budget', 'key'}] in queue order."""
    path = qdir / 'queue.tsv'
    if not path.is_file():
        raise QueueError(f'{path} does not exist')
    units = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip() or line.startswith('#'):
            continue
        cols = line.split('\t')
        if len(cols) != 4:
            raise QueueError(f'{path}:{n}: expected 4 tab-separated columns, found {len(cols)}')
        d, sources, functions, budget = cols
        units.append({'dir': d, 'sources': [s for s in sources.split(',') if s],
                      'functions': [f for f in functions.split(',') if f], 'budget': int(budget),
                      'key': Path(d).name})
    return units


def now():
    return time.time()


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def read_claim(path):
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        # A claim being written right now, or a damaged one: fall back to the file time.
        try:
            return {'time': path.stat().st_mtime}
        except OSError:
            return None


def try_create(path, worker, t, profile=None):
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return False
    with os.fdopen(fd, 'w') as out:
        json.dump({'worker': worker, 'time': t, 'claimed': iso(t), 'pid': os.getpid(), 'profile': profile}, out)
    return True


def set_aside_near_misses(unit_dir, t, repo=REPO):
    """Move near-miss files of an earlier session into near-miss/earlier-<time>/; returns that dir."""
    d = Path(unit_dir)
    nm = (d if d.is_absolute() else repo / d) / 'near-miss'
    if not nm.is_dir():
        return None
    loose = [f for f in nm.iterdir() if f.is_file()]
    if not loose:
        return None
    dest = nm / f'earlier-{dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")}'
    dest.mkdir(exist_ok=True)
    for f in loose:
        os.replace(f, dest / f.name)
    return dest


def claim(qdir, worker, t=None, profile=None, repo=REPO):
    """Claim a unit for `worker`: its own unfinished claim first, then the first unclaimed unit,
    then the first stale claim. Returns the unit dict, or None when nothing is left to claim."""
    if not LABEL.fullmatch(worker or ''):
        raise QueueError('--worker must be a label like luna56-medium-1 (letters, digits, . _ -)')
    t = now() if t is None else t
    u = _claim(qdir, worker, t, profile)
    if u is not None and not u.get('resumed'):
        u['earlier_near_misses'] = set_aside_near_misses(u['dir'], t, repo)
    return u


def _claim(qdir, worker, t, profile):
    units = read_queue(qdir)
    claims, done = qdir / 'claims', qdir / 'done'
    claims.mkdir(parents=True, exist_ok=True)
    done.mkdir(parents=True, exist_ok=True)
    open_units = [u for u in units if not (done / f'{u["key"]}.json').exists()]
    for u in open_units:  # a restarted session resumes its own unit
        c = read_claim(claims / f'{u["key"]}.lock')
        if c and c.get('worker') == worker:
            return dict(u, resumed=True)
    for u in open_units:
        if try_create(claims / f'{u["key"]}.lock', worker, t, profile):
            return u
    for u in open_units:
        lock = claims / f'{u["key"]}.lock'
        c = read_claim(lock)
        if c is None or t - float(c.get('time', t)) < STALE_SECONDS:
            continue
        tomb = claims / f'{u["key"]}.stale-{int(t)}-{os.getpid()}'
        try:
            os.rename(lock, tomb)  # only one of several racing sessions wins this
        except FileNotFoundError:
            continue
        tomb.unlink(missing_ok=True)
        if try_create(lock, worker, t, profile):
            return u
    return None


@contextlib.contextmanager
def locked(path):
    with open(path, 'a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield handle
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def find_unit(qdir, unit_dir):
    key = Path(unit_dir.rstrip('/')).name
    for u in read_queue(qdir):
        if u['key'] == key:
            return u
    raise QueueError(f'{unit_dir} is not a unit of {qdir / "queue.tsv"}')


def finish(qdir, unit_dir, lines, worker=None, t=None):
    """Record result lines for a unit, mark it done and release its claim. Returns the records."""
    t = now() if t is None else t
    u = find_unit(qdir, unit_dir)
    lock = qdir / 'claims' / f'{u["key"]}.lock'
    c = read_claim(lock) if lock.exists() else None
    worker = worker or (c or {}).get('worker')
    if not worker:
        raise QueueError(f'{u["dir"]} is not claimed; pass --worker <label> to record a result anyway')
    stamp = {'profile': (c or {}).get('profile')}
    if c and c.get('time') is not None:
        stamp['claimed'] = iso(float(c['time']))
    if not lines:
        raise QueueError('give at least one --result line (one per function, then one for the unit)')
    records = []
    for raw in lines:
        try:
            rec = json.loads(raw)
        except ValueError as exc:
            raise QueueError(f'--result is not one JSON object: {exc}: {raw[:120]}') from None
        if not isinstance(rec, dict) or not ({'rva', 'result'} <= rec.keys() or 'unit' in rec or 'task' in rec):
            raise QueueError('each --result needs "rva" and "result" (a function line) or "unit" (the unit line)')
        records.append(dict(rec, worker=worker, queue_unit=u['dir'], recorded=iso(t), **stamp))
    (qdir / 'done').mkdir(parents=True, exist_ok=True)
    with locked(qdir / 'results.lock'):
        with open(qdir / 'results.jsonl', 'a') as out:
            for rec in records:
                out.write(json.dumps(rec, sort_keys=True) + '\n')
        (qdir / 'done' / f'{u["key"]}.json').write_text(json.dumps({'worker': worker, 'done': iso(t)}) + '\n')
        lock.unlink(missing_ok=True)
    return records


def release(qdir, unit_dir, worker=None, t=None):
    """Give back a claim without a result, so another session can take the unit at once.

    With `worker`, refuses a claim held by another label: a session releases only its own claim
    (or names the holder deliberately)."""
    t = now() if t is None else t
    u = find_unit(qdir, unit_dir)
    lock = qdir / 'claims' / f'{u["key"]}.lock'
    if (qdir / 'done' / f'{u["key"]}.json').exists():
        raise QueueError(f'{u["dir"]} is already done; nothing to release')
    c = read_claim(lock) if lock.exists() else None
    if c is None:
        raise QueueError(f'{u["dir"]} is not claimed')
    if worker and c.get('worker') not in (None, worker):
        raise QueueError(f'{u["dir"]} is claimed by {c.get("worker")}, not {worker}')
    with locked(qdir / 'results.lock'):
        with open(qdir / 'releases.jsonl', 'a') as out:
            out.write(json.dumps({'queue_unit': u['dir'], 'worker': c.get('worker'), 'profile': c.get('profile'),
                                  'claimed': iso(float(c.get('time', t))), 'released': iso(t)}, sort_keys=True) + '\n')
        lock.unlink(missing_ok=True)
    return c.get('worker')


def unit_line(unit_dir, repo=REPO):
    """The queue.tsv line of a unit task dir: its sources, functions and remaining counted attempts."""
    d = Path(unit_dir)
    task = json.loads(((d if d.is_absolute() else repo / d) / 'task.json').read_text())
    cpp = task['compiled']
    log = (d if d.is_absolute() else repo / d) / 'attempts.jsonl'
    used = 0
    if log.is_file():
        used = sum(1 for line in log.read_text().splitlines() if line.strip() and json.loads(line).get('counted'))
    budget = (task.get('max_attempts') or 0) - used
    rel = d.relative_to(repo).as_posix() if d.is_absolute() else d.as_posix()
    functions = ','.join(str(f['rva']) for f in task.get('functions') or [])
    return f'{rel}\t{cpp[:-4]}.h,{cpp}\t{functions}\t{budget}', budget


def add(qdir, dirs, repo=REPO):
    """Append unit task dirs (a group dir adds all its units) that are not queued yet."""
    qdir.mkdir(parents=True, exist_ok=True)
    path = qdir / 'queue.tsv'
    have = {u['key'] for u in read_queue(qdir)} if path.is_file() else set()
    units = []
    for arg in dirs:
        d = Path(arg.rstrip('/'))
        full = d if d.is_absolute() else repo / d
        if (full / 'group.json').is_file():
            units += [d / u['dir'] for u in json.loads((full / 'group.json').read_text())['units']]
        elif (full / 'task.json').is_file():
            units.append(d)
        else:
            raise QueueError(f'{arg} has neither task.json nor group.json')
    added = []
    with locked(qdir / 'results.lock'):
        with open(path, 'a') as out:
            if not have and path.stat().st_size == 0:
                out.write('# unit dir\tsources\tfunctions\tcounted attempts left\n')
            for d in units:
                if d.name in have:
                    continue
                line, budget = unit_line(d, repo)
                if budget <= 0:
                    raise QueueError(f'{d}: no counted attempts left; raise max_attempts in its task.json first')
                out.write(line + '\n')
                have.add(d.name)
                added.append(d.as_posix())
    return added


def status(qdir, t=None):
    t = now() if t is None else t
    rows = []
    for u in read_queue(qdir):
        if (qdir / 'done' / f'{u["key"]}.json').exists():
            state, who = 'done', json.loads((qdir / 'done' / f'{u["key"]}.json').read_text()).get('worker')
        else:
            c = read_claim(qdir / 'claims' / f'{u["key"]}.lock') if (qdir / 'claims' / f'{u["key"]}.lock').exists() else None
            if c is None:
                state, who = 'open', ''
            else:
                age = t - float(c.get('time', t))
                state, who = ('stale' if age >= STALE_SECONDS else 'claimed'), c.get('worker', '?')
        rows.append((state, who, u))
    return rows


def model_of(label):
    return re.sub(r'-\d+$', '', label or '?')


def stats(qdir):
    """{'worker': {label: summary}, 'model': {model: summary}} from results.jsonl."""
    path = qdir / 'results.jsonl'
    recs = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    out = {kind: defaultdict(lambda: defaultdict(int)) for kind in ('worker', 'model', 'profile')}
    for r in recs:
        for kind, key in (('worker', r.get('worker')), ('model', model_of(r.get('worker'))),
                          ('profile', r.get('profile') or 'unrecorded')):
            s = out[kind][key]
            if 'rva' in r:
                s['functions'] += 1
                s['passed'] += r.get('result') == 'pass'
                s['attempts'] += int(r.get('attempts') or 0)
            elif 'unit' in r or 'task' in r:
                s['units'] += 1
    result = {}
    for kind, table in out.items():
        result[kind] = {}
        for key, s in sorted(table.items()):
            f = s['functions']
            result[kind][key] = {'units': s['units'], 'functions': f, 'passed': s['passed'],
                                 'pass_rate': round(s['passed'] / f, 3) if f else None,
                                 'attempts_per_function': round(s['attempts'] / f, 2) if f else None}
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--queue-dir', help='default $SKYRIM_QUEUE_DIR or .local/queue/small')
    sub = p.add_subparsers(dest='cmd', required=True)
    n = sub.add_parser('next', help='claim the next unit and print its unit dir (EMPTY when none is left)')
    n.add_argument('--worker', required=True, help='model, effort and session number, e.g. luna56-medium-1')
    n.add_argument('--profile', choices=('cheap', 'full'), help='drafting profile (tools/profiles.py); recorded with the results')
    r = sub.add_parser('release', help='give back a claimed unit you will not work on')
    r.add_argument('unit_dir')
    r.add_argument('--worker', help='your label; refuses a claim held by another label')
    d = sub.add_parser('done', help='record result lines for a unit and release it')
    d.add_argument('unit_dir')
    d.add_argument('--result', action='append', default=[], help='one JSON line; repeat for each line')
    d.add_argument('--worker', help='only when the unit has no claim (default: the claim\'s label)')
    sub.add_parser('status')
    sub.add_parser('stats')
    ad = sub.add_parser('add', help='append unit or group task dirs to the queue (queue order = order given)')
    ad.add_argument('dirs', nargs='+')
    a = p.parse_args(argv)
    qdir = queue_dir(a.queue_dir)
    try:
        if a.cmd == 'next':
            u = claim(qdir, a.worker, profile=a.profile)
            if u is None:
                busy = sum(1 for state, _, _ in status(qdir) if state == 'claimed')
                print('EMPTY' + (f' ({busy} unit(s) still claimed by other sessions)' if busy else ''))
                return 0
            print(u['dir'])
            if u.get('earlier_near_misses'):
                print(f'# near-miss files of an earlier session moved to {u["earlier_near_misses"]}; they may not '
                      'match the current unit source', file=sys.stderr)
            print(f'# sources: {" ".join(u["sources"])}; functions: {" ".join(u["functions"])}; '
                  f'budget: {u["budget"]} counted attempts', file=sys.stderr)
            return 0
        if a.cmd == 'done':
            recs = finish(qdir, a.unit_dir, a.result, a.worker)
            print(f'recorded {len(recs)} line(s) for {recs[0]["queue_unit"]} as {recs[0]["worker"]}; '
                  'next: python3 tools/work_queue.py next --worker ' + recs[0]['worker'])
            return 0
        if a.cmd == 'release':
            holder = release(qdir, a.unit_dir, a.worker)
            print(f'released {a.unit_dir} (was claimed by {holder})')
            return 0
        if a.cmd == 'status':
            rows = status(qdir)
            counts = defaultdict(int)
            for state, who, u in rows:
                counts[state] += 1
                if state != 'open':
                    print(f'{state:8s} {who:24s} {u["dir"]}')
            print(json.dumps({'units': len(rows), **counts,
                              'functions': sum(len(u['functions']) for _, _, u in rows)}))
            return 0
        if a.cmd == 'add':
            added = add(qdir, a.dirs)
            print(f'added {len(added)} unit(s) to {qdir / "queue.tsv"}')
            return 0
        if a.cmd == 'stats':
            print(json.dumps(stats(qdir), indent=2))
            return 0
    except QueueError as exc:
        print(f'queue: {exc}', file=sys.stderr)
        return 2
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
