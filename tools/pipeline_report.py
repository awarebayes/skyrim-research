#!/usr/bin/env python3
"""Read-only pipeline timings, queue, funnel, stalls and refusal counts.

    python3 tools/pipeline_report.py --root <shared-checkout> --flow-dir <shared-flow>
    python3 tools/pipeline_report.py --json [--output <file>]

Never creates locks, fetches refs, changes scheduling state or saves a cache. Git's
existing origin/main ref supplies pushed state. GitHub queries are read-only;
--offline skips them. Missing historical timestamps remain unknown. Estimates
from log creation/mtime and receipt mtime are labelled, not match evidence.
"""
import argparse
from collections import Counter
import datetime as dt
import fcntl
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
import flow

STATES = ('queued', 'drafting', 'drafted', 'confirmed', 'review pending',
          'approved', 'accepted', 'pushed')
REASONS = ('harvest differs from confirmed record', 'unfinished tooling publication',
           'already running', 'origin changed carried files', 'gate state changed',
           'queued input changed', 'incompatible queued inputs', 'sampling gate',
           'blocking escalation', 'no approvals', 'saved review', 'insufficient free disk',
           'origin CI is not green', 'whole tree failed', 'candidate changed',
           'origin kept moving', 'no tooling commit to push', 'tooling CI',
           'CI RED', 'CI PENDING', 'STOPPED at', 'refusing', 'refused')


def stamp(value):
    if isinstance(value, (float, int)):
        return float(value) if math.isfinite(value) and value > 0 else None
    try:
        return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except (AttributeError, TypeError, ValueError):
        return None


def iso(value):
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z') if value is not None else None


def elapsed(start, end):
    return end - start if start is not None and end is not None and end >= start else None


def ident(value):
    """Only operational identifiers, never paths or arbitrary receipt payloads."""
    value = str(value or '')
    return value if re.fullmatch(r'[A-Za-z0-9_.:@+-]{1,140}', value) else 'unknown'


def safe_text(value):
    text = re.sub(r'https?://\S+|(?<![\w])(?:[A-Za-z]:[\\/]|/|~/)\S+', '[path]', str(value))
    text = re.sub(r'\\x[0-9a-fA-F]{2}|\b[0-9a-fA-F]{32,}\b', '[redacted]', text)
    return ' '.join(text.split())[:180]


def reason(value):
    return next((r for r in REASONS if r.lower() in str(value).lower()), 'other (details withheld)')


def owner(value):
    if isinstance(value, dict):
        return ident(value.get('task_id') or value.get('worker') or value.get('label') or
                     ('pid:' + str(value['pid']) if value.get('pid') else None))
    return ident(value)


def mtime(path):
    try:
        return Path(path).stat().st_mtime
    except OSError:
        return None


def created(path):
    try:
        s = Path(path).stat()
        # ctime is inode-change time, not creation time on Unix.
        return getattr(s, 'st_birthtime', None)
    except OSError:
        return None


def read(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def json_rows(directory):
    return [(p, r) for p in sorted(Path(directory).glob('*.json'))
            if isinstance(r := read(p), dict)]


def json_lines(path):
    try:
        lines = Path(path).read_text(errors='replace').splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            r = json.loads(line)
            if isinstance(r, dict):
                out.append(r)
        except ValueError:
            pass  # An append may be in flight; never repair it.
    return out


def command(args, root):
    try:
        p = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=30)
        return p.stdout if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def shared_root(root):
    common = command(['git', 'rev-parse', '--git-common-dir'], root)
    if common:
        return (Path(root) / common.strip()).resolve().parent
    return Path(root)


def lock_busy(fdir):
    """Probe an existing inode read-only; unlike flow.running, never creates it."""
    try:
        with (fdir / 'lane/.lane.lock').open('rb') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(stream, fcntl.LOCK_UN)
                return False
            except BlockingIOError:
                return True
    except FileNotFoundError:
        return False
    except OSError:
        return None


def github_jobs(root, commits):
    """One list query plus one job query per relevant exact-SHA workflow run."""
    raw = command(['gh', 'run', 'list', '--limit', '100', '--json',
                   'databaseId,headSha,workflowName,createdAt,startedAt,updatedAt,status,conclusion'], root)
    try:
        runs = json.loads(raw) if raw else []
    except ValueError:
        runs = []
    out = {}
    for run in runs:
        sha = run.get('headSha')
        if sha not in commits:
            continue
        raw = command(['gh', 'run', 'view', str(run['databaseId']), '--json', 'jobs'], root)
        try:
            jobs = json.loads(raw).get('jobs', []) if raw else []
        except ValueError:
            jobs = []
        for job in jobs:
            out.setdefault(sha, []).append(dict(run_id=run['databaseId'], job=safe_text(job.get('name') or 'unknown'),
                start=iso(stamp(job.get('startedAt'))), end=iso(stamp(job.get('completedAt'))),
                outcome=ident(job.get('conclusion') or job.get('status')), source='gh exact-SHA job'))
    return out


def point(value, source):
    return dict(at=iso(value), source=source if value is not None else 'unknown')


def timeline_row(path, receipt, kind, jobs):
    integ = receipt.get('integrated') or {}
    attempts = list(receipt.get('attempts', []))
    if integ:
        # Tooling attempts store only commit/base/logs; integration attempts are checkpoints.
        if attempts and attempts[-1].get('commit') == integ.get('commit'):
            attempts[-1] = dict(attempts[-1], **integ)
        else:
            attempts.append(integ)
    stages = []
    for i, attempt in enumerate(attempts):
        logs = attempt.get('logs')
        if not logs and i == len(attempts) - 1:
            logs = receipt.get('checks_log_dir')
        end = stamp(attempt.get('checks'))
        duration = attempt.get('wall_seconds', {}).get('checks')
        start = end - duration if end is not None and isinstance(duration, (int, float)) else None
        for name in ('check', 'tests', 'site'):
            log = Path(logs) / (name + '.log') if logs else None
            log_end = mtime(log) if log else None
            log_start = created(log) if log else None
            # A completed preceding log is a proxy for the next command start.
            source = 'log birthtime estimate'
            if log_start is None and log_end is not None:
                log_start, source = start, 'previous log mtime / wall-seconds estimate'
            stages.append(dict(attempt=i + 1, stage=name,
                               start=point(log_start, source), end=point(log_end, 'log mtime estimate')))
            if log_end is not None:
                start = log_end
    checks_end = stamp(integ.get('checks'))
    wall = integ.get('wall_seconds') or {}
    checks_start = (checks_end - wall['checks'] if checks_end is not None and isinstance(wall.get('checks'), (int, float))
                    else next((stamp(s['start']['at']) for s in stages if s['start']['at']), None))
    acquired = stamp(receipt.get('lock_acquired_at') or receipt.get('acquired_at') or receipt.get('started_at'))
    acquired_source = 'receipt'
    if acquired is None:
        acquired = checks_start
        if acquired is not None:
            acquired -= wall.get('build', 0)
        acquired_source = 'checks/build lower-bound estimate (setup and earlier attempts may be missing)'
    queued = stamp(receipt.get('queued_at'))
    if queued is None:
        times = [stamp(i.get('queued_at')) for i in receipt.get('items', [])]
        queued = min((t for t in times if t is not None), default=None)
    released = stamp(receipt.get('released_at') or receipt.get('finished_at') or receipt.get('retired_at'))
    released_source = 'receipt'
    if released is None and receipt.get('state') in ('done', 'retired', 'failed'):
        released, released_source = mtime(path), 'receipt mtime estimate (may include later updates)'
    pushed = stamp(integ.get('pushed'))
    ci_jobs = jobs.get(integ.get('commit'), [])
    starts = [stamp(j.get('start')) for j in ci_jobs]
    ends = [stamp(j.get('end')) for j in ci_jobs]
    ci_start = min((t for t in starts if t is not None), default=None)
    ci_end = max((t for t in ends if t is not None), default=None) if ends and all(t is not None for t in ends) else None
    ci_source = 'gh exact-SHA jobs'
    if ci_start is None:
        ci_start, ci_source = pushed, 'push to CI-log/receipt mtime estimate (includes queue/wait)'
        ci_end = mtime(receipt['ci_log']) if receipt.get('ci_log') else (released if integ.get('ci') == 'green' else None)
    if (released_source.startswith('receipt mtime') and ci_jobs and ci_end is not None
            and released is not None and released > ci_end + 120):
        released, released_source = ci_end, 'CI completion lower-bound estimate (receipt updated later)'
    functions = sorted({ident(r) for req in receipt.get('accepted', []) for r in req.get('functions', [])})
    hold, wait, ci_seconds = elapsed(acquired, released), elapsed(queued, acquired), elapsed(ci_start, ci_end)
    # Public job finish may be after a stale receipt, or a receipt may have been backfilled.
    share = ci_seconds / hold if hold and ci_seconds is not None and ci_seconds <= hold else None
    return dict(id=ident(receipt.get('id', path.stem)), kind=kind, owner=owner(receipt.get('owner')),
                outcome=ident(receipt.get('state')), ci=ident(integ.get('ci')),
                functions=functions, function_count=len(functions) or integ.get('accepted', 0),
                queued_at=point(queued, 'receipt/items'), lock_acquired=point(acquired, acquired_source),
                checks_start=point(checks_start, 'recorded wall-seconds/log estimate'),
                checks_end=point(checks_end, 'receipt'), stages=stages,
                push=point(pushed, 'receipt'), ci_start=point(ci_start, ci_source), ci_end=point(ci_end, ci_source),
                ci_jobs=ci_jobs, released_at=point(released, released_source),
                hold_seconds=hold, wait_seconds=wait, ci_seconds=ci_seconds, ci_share=share,
                updated_at=iso(mtime(path)))


def distribution(values):
    values = sorted(v for v in values if v is not None and math.isfinite(v))
    return dict(n=len(values), median=statistics.median(values) if values else None,
                p90=values[max(0, math.ceil(len(values) * .9) - 1)] if values else None)


def process_waiters(root, fdir):
    """Legacy waiters have no receipt. Inspect only commands targeting this shared flow."""
    output = command(['ps', '-axo', 'pid=,etime=,command='], root) or ''
    out = []
    for line in output.splitlines():
        parts = line.split(None, 2)
        if len(parts) != 3 or not parts[0].isdigit():
            continue
        pid, age, cmd = parts
        if 'flow.py' not in cmd or 'tooling-push' not in cmd or '--wait-lane' not in cmd:
            continue
        if str(fdir) not in cmd:
            continue
        try:
            days, clock = age.split('-', 1) if '-' in age else ('0', age)
            fields = [int(n) for n in clock.split(':')]
            seconds = int(days) * 86400 + sum(n * 60 ** i for i, n in enumerate(reversed(fields)))
        except ValueError:
            seconds = None
        out.append(dict(id='pid:' + pid, kind='tooling-process', owner='pid:' + pid,
                        age_seconds=seconds, age_source='process age, upper bound on wait'))
    return out


def funnel(root, fdir, now):
    # This function reads existing refs; flow's "online" flag does not fetch.
    states = flow.function_states(root, fdir, online=True)
    gs = flow.groups(fdir)
    by_rva = {flow.hexrva(fn['rva']): fn for fn in flow.inventory(root)['functions']}
    claims, results = {}, {}
    for qdir, _, unit, _, _, claim in flow.queue_units(root):
        for rva in unit['functions']:
            claims[flow.hexrva(rva)] = (claim or {}, mtime(qdir / 'queue.tsv'))
    for r in flow.queue_results(root):
        if 'rva' in r:
            results[flow.hexrva(r['rva'])] = r
    out = {s: dict(count=0, oldest_seconds=None, buckets=Counter(), age_sources=Counter()) for s in STATES}
    for rva, row in states.items():
        raw_state = row['state'] or 'unknown'
        state = {'drafted-pass': 'drafted', 'review-pending': 'review pending'}.get(raw_state, ident(raw_state))
        g = gs.get(row.get('group'), {})
        fn = by_rva.get(rva, {})
        since, source = None, 'unknown'
        if state in ('approved', 'rejected', 'escalated') and g:
            try:
                since = mtime(flow.review_path(root, g))
            except (ValueError, flow.FlowError):
                pass
            source = 'review mtime proxy'
        elif state == 'review pending':
            since, source = stamp(g.get('created')), 'group created proxy'
        elif state in ('accepted', 'pushed', 'confirmed', 'confirm-stale'):
            name = fn.get('report')
            if name:
                p = root / name
                if state in ('accepted', 'pushed'):
                    p = p.with_suffix('.review.json')
                since, source = mtime(p), 'record mtime proxy'
        elif state == 'drafting':
            c, _ = claims.get(rva, ({}, None))
            since, source = stamp(c.get('claimed') or c.get('time')), 'claim time'
        elif state in ('drafted', 'draft-failed'):
            r = results.get(rva, {})
            since, source = stamp(r.get('recorded') or r.get('time') or r.get('released')), 'result time'
        elif state == 'queued':
            _, since = claims.get(rva, ({}, None))
            source = 'queue mtime proxy'
        age = elapsed(since, now)
        bucket = 'unknown' if age is None else '<90m' if age < 5400 else '90m-6h' if age < 21600 else '6h-24h' if age < 86400 else '>=24h'
        s = out.setdefault(state, dict(count=0, oldest_seconds=None, buckets=Counter(), age_sources=Counter()))
        s['count'] += 1
        s['buckets'][bucket] += 1
        s['age_sources'][source if age is not None else 'unknown'] += 1
        if age is not None:
            s['oldest_seconds'] = max(s['oldest_seconds'] or 0, age)
    return out


def last_next_step(path):
    try:
        lines = path.read_text(errors='replace').splitlines()
    except OSError:
        return 'unknown'
    candidates, fenced, heading = [], False, False
    for line in lines:
        if line.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if fenced:
            continue
        if re.match(r'^#{1,6}\s+', line):
            heading = bool(re.search(r'\bnext\b', line, re.I))
            continue
        if re.search(r'\bnext(?:[ _-]+step)?\s*(?:[:|]|\*\*)', line, re.I):
            candidates.append(line)
        elif heading and line.strip():
            candidates.append(line)
            heading = False
    return safe_text(candidates[-1]) if candidates else 'unknown'


def refusals(receipts, logs, now):
    counts, sources = Counter(), Counter()
    for path, r in receipts:
        # Repeated copies of a dropped array are not distinct events. Count each
        # entry once per run; error is a separate persisted run-level refusal.
        at = stamp(r.get('updated_at') or r.get('finished_at')) or mtime(path)
        if at is None or not now - 86400 <= at <= now:
            continue
        for field in ('dropped', 'held'):
            values = r.get(field) or []
            if isinstance(values, dict):
                values = list(values.values())
            if not isinstance(values, list):
                values = [values]
            for item in values:
                counts[reason(item.get('reason') if isinstance(item, dict) else item)] += 1
                sources['receipt ' + field] += 1
        if r.get('error'):
            counts[reason(r['error'])] += 1
            sources['receipt error'] += 1
    for path in logs:
        at = mtime(path)
        if at is None or not now - 86400 <= at <= now:
            continue
        try:
            lines = path.read_text(errors='replace').splitlines()
        except OSError:
            continue
        for line in lines:
            # Only operational refusal lines, never full test/check output.
            if re.search(r'(?:^flow:|already running|unfinished tooling publication|harvest differs from confirmed record)', line, re.I):
                counts[reason(line)] += 1
                sources['log observation'] += 1
    return dict(window_hours=24, counts=dict(counts.most_common()), sources=dict(sources),
                coverage='receipt/log-mtime window; observations, not unique attempts; unlogged refusals unavailable')


def report(root, fdir, handoffs, now=None, offline=False, inspect_processes=True, log_paths=()):
    root, fdir, handoffs = Path(root), Path(fdir), Path(handoffs)
    now = time.time() if now is None else now
    receipts = [(p, r) for d in ('runs', 'tooling') for p, r in json_rows(fdir / 'lane' / d)]
    commits = {(r.get('integrated') or {}).get('commit') for _, r in receipts} - {None}
    jobs = {} if offline else github_jobs(root, commits)
    timeline = sorted([timeline_row(p, r, 'tooling' if p.parent.name == 'tooling' else 'lane', jobs)
                       for p, r in receipts], key=lambda r: r['lock_acquired']['at'] or '')
    summary = {field: distribution(r[field] for r in timeline if r['outcome'] == 'done')
               for field in ('hold_seconds', 'wait_seconds', 'ci_share')}
    busy, holder = lock_busy(fdir), read(fdir / 'lane/owner.json', {})
    active = next((r for r in reversed(timeline) if r['outcome'] == 'running' and
                   r['owner'] == owner(holder)), None) if busy else None
    start = stamp(holder.get('acquired_at') or holder.get('started_at'))
    start_source = 'owner receipt'
    if start is None and active:
        start, start_source = stamp(active['lock_acquired']['at']), active['lock_acquired']['source']
    if start is None and busy and holder.get('birth'):
        try:
            start = dt.datetime.strptime(holder['birth'], '%a %b %d %H:%M:%S %Y').astimezone().timestamp()
            start_source = 'process birth, upper bound on lock age'
        except (ValueError, TypeError):
            pass
    waiting = []
    for p, r in json_rows(fdir / 'lane/queue'):
        if r.get('state') == 'queued':
            waiting.append(dict(id=ident(r.get('id', p.stem)), kind=ident(r.get('kind')), owner=owner(r.get('owner') or (Path(r['root']).name if r.get('root') else None)),
                                age_seconds=elapsed(stamp(r.get('queued_at')), now), age_source='queued_at'))
    for row in timeline:
        if row['outcome'] in ('queued', 'waiting'):
            waiting.append(dict(id=row['id'], kind='tooling', owner=row['owner'],
                                age_seconds=elapsed(stamp(row['queued_at']['at']), now), age_source='queued_at'))
    for directory in ('waiters', 'tooling-waiters'):
        for p, r in json_rows(fdir / 'lane' / directory):
            if r.get('state', 'waiting') in ('queued', 'waiting'):
                waiting.append(dict(id=ident(r.get('id', p.stem)), kind=ident(r.get('kind', 'tooling')),
                                    owner=owner(r.get('owner')), age_seconds=elapsed(stamp(r.get('queued_at')), now), age_source='queued_at'))
    if inspect_processes:
        known = {w['owner'] for w in waiting} | ({owner(holder)} if busy else set())
        waiting.extend(w for w in process_waiters(root, fdir) if w['owner'] not in known)
    tooling = sum(w['kind'].startswith('tooling') for w in waiting)
    batches = tooling + int(any(not w['kind'].startswith('tooling') for w in waiting))
    median = summary['hold_seconds']['median']
    held_age = elapsed(start, now) if busy else None
    remaining = max(0, median - held_age) if median is not None and held_age is not None else median if busy else 0
    drain = (batches * median + remaining if median is not None and remaining is not None else None)
    progress_times = [stamp(r[k]['at']) for r in timeline for k in ('checks_end', 'push', 'ci_end', 'released_at')]
    last_progress = max((t for t in progress_times if t is not None), default=None)
    workers = []
    for p in sorted(handoffs.glob('*.md')):
        modified = mtime(p)
        age = elapsed(modified, now)
        workers.append(dict(id=ident(p.stem), age_seconds=age, next_step=last_next_step(p),
                            stalled=bool(age is not None and age > 5400 and (last_progress is None or last_progress <= modified))))
    logs = list((fdir / 'lane').glob('*.log')) + list((fdir / 'lane/tooling').glob('**/*.log'))
    logs += list(handoffs.glob('*.log')) + [Path(p) for p in log_paths]
    logs = sorted(set(logs))
    return dict(generated_at=iso(now), timeline=timeline, summary=summary,
        queue=dict(busy=busy, holder=owner(holder) if busy else None, run=active['id'] if active else None,
                   held_seconds=held_age, held_source=start_source, waiting=waiting,
                   estimated_batches=batches, drain_seconds=drain,
                   assumptions='one batch for queued acceptance entries; one per tooling waiter; current hold residual uses median; unrecorded waiters unavailable'),
        funnel=funnel(root, fdir, now), workers=workers, refusals=refusals(receipts, logs, now),
        limitations=['Read-only non-atomic snapshot; concurrent changes can cross sections.',
                     'Historical hold/release and state ages may be mtime proxies, not recorded transitions.',
                     'Existing origin/main ref only (no fetch); GitHub limited to 100 recent runs; offline skips job queries.',
                     'Stall flag means handoff >90m and no global lane milestone after that handoff; not a worker heartbeat.'])


def duration(value):
    return '?' if value is None else f'{value / 3600:.1f}h' if value >= 3600 else f'{value / 60:.1f}m'


def table(headers, rows):
    values = [headers] + [[str(v) for v in row] for row in rows]
    widths = [max(len(row[i]) for row in values) for i in range(len(headers))]
    return '\n'.join('  '.join(v.ljust(w) for v, w in zip(row, widths)).rstrip() for row in values)


def render(data):
    lines = ['Pipeline report ' + data['generated_at'],
             'Times UTC; ? unknown; ~ inferred from logs/wall durations/receipt mtime. JSON carries sources and all stage/job times.']
    def at(p):
        return (p['at'] or '?') + ('~' if 'estimate' in p['source'] else '')
    lines += [table(['KIND/ID', 'OWNER', 'QUEUED', 'ACQUIRED', 'CHECKS START/END', 'PUSH', 'CI START/END', 'RELEASED', 'HOLD', 'WAIT', 'FUNCS', 'OUTCOME'],
                   [[r['kind'] + '/' + r['id'], r['owner'], at(r['queued_at']), at(r['lock_acquired']),
                     at(r['checks_start']) + '/' + at(r['checks_end']), at(r['push']), at(r['ci_start']) + '/' + at(r['ci_end']),
                     at(r['released_at']), duration(r['hold_seconds']), duration(r['wait_seconds']), r['function_count'], r['outcome'] + '/' + r['ci']] for r in data['timeline']])]
    for r in data['timeline']:
        for s in r['stages']:
            if s['start']['at'] or s['end']['at']:
                lines.append(f"  {r['id']} attempt {s['attempt']} {s['stage']}: {at(s['start'])} -> {at(s['end'])}")
        for j in r['ci_jobs']:
            lines.append(f"  {r['id']} CI run {j['run_id']} job {j['job']}: {j['start'] or '?'} -> {j['end'] or '?'} {j['outcome']}")
    lines.append(table(['DONE SUMMARY (includes estimates)', 'N', 'MEDIAN', 'P90'],
        [[k, v['n'], (f"{v['median']:.0%}" if v['median'] is not None else '?') if k == 'ci_share' else duration(v['median']),
          (f"{v['p90']:.0%}" if v['p90'] is not None else '?') if k == 'ci_share' else duration(v['p90'])] for k, v in data['summary'].items()]))
    q = data['queue']
    lines.append(f"LANE busy={q['busy']} holder={q['holder'] or '?'} run={q['run'] or '?'} held={duration(q['held_seconds'])} ({q['held_source']}); waiting={len(q['waiting'])}; drain~{duration(q['drain_seconds'])} ({q['estimated_batches']} batches)")
    lines.append(q['assumptions'])
    lines.append(table(['WAITING', 'KIND', 'OWNER', 'AGE', 'AGE SOURCE'], [[w['id'], w['kind'], w['owner'], duration(w['age_seconds']), w['age_source']] for w in q['waiting']]))
    lines.append(table(['FUNCTION STATE', 'COUNT', 'OLDEST (proxy)', '<90m', '90m-6h', '6h-24h', '>=24h', 'UNKNOWN'],
        [[s, v['count'], duration(v['oldest_seconds']), *[v['buckets'].get(b, 0) for b in ('<90m', '90m-6h', '6h-24h', '>=24h', 'unknown')]] for s, v in data['funnel'].items()]))
    lines.append(table(['HANDOFF', 'AGE', 'STALL', 'LAST NEXT STEP'],
                       [[w['id'], duration(w['age_seconds']), 'YES' if w['stalled'] else '-', w['next_step']] for w in data['workers']]))
    lines.append(table(['REFUSALS/HOLDS (24h observations)', 'COUNT'], list(data['refusals']['counts'].items())))
    lines.append(data['refusals']['coverage'])
    lines.extend('Note: ' + s for s in data['limitations'])
    return '\n'.join(lines) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--root', type=Path, help='state checkout (default: shared checkout of this worktree)')
    p.add_argument('--flow-dir', type=Path)
    p.add_argument('--handoffs', type=Path)
    p.add_argument('--log', type=Path, action='append', default=[], help='additional operational refusal log (repeatable)')
    p.add_argument('--json', action='store_true')
    p.add_argument('--offline', action='store_true')
    p.add_argument('--output', type=Path, help='only file this command writes; parent must exist')
    a = p.parse_args(argv)
    shared = shared_root(a.root or Path(__file__).resolve().parents[1])
    root = a.root or shared
    fdir = a.flow_dir or Path(os.environ.get('SKYRIM_FLOW_DIR') or shared / '.local/flow')
    try:
        data = report(root, fdir, a.handoffs or shared / '.local/handoffs', offline=a.offline, log_paths=a.log)
        output = json.dumps(data, indent=2) + '\n' if a.json else render(data)
        if a.output:
            a.output.write_text(output)
        else:
            print(output, end='')
        return 0
    except (OSError, ValueError, flow.FlowError) as error:
        print('pipeline report unavailable: ' + reason(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
