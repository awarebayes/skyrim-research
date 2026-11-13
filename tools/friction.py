#!/usr/bin/env python3
"""Friction report from the work queues, the pipeline state and the saved reviews.

    python3 tools/friction.py                 # print the report
    python3 tools/friction.py --write         # also save .local/flow/friction-<time>.md and log the event
    python3 tools/friction.py --json

Per model and per profile: functions, pass rate, attempts per passing function, units, abandoned
units (finished with no pass, or released), stalls (claims held past the look threshold now), and
wall time per unit (claim to result). Then rejects by reason (failed checks and blocking findings
in saved reviews of flow groups and earlier reviews), and the most frequent failure messages
(fail reasons, blockers and friction notes the workers recorded).

It reads only private ledgers under `.local/` and writes only under `.local/flow/`. It decides
nothing: the routine orchestrator produces it once per work session and a direction check reads it.
"""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import json
from pathlib import Path
import re
import statistics
import sys
import time

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import accept_function as af  # noqa: E402
import flow  # noqa: E402
import profiles  # noqa: E402
import work_queue as wq  # noqa: E402

ROOT = TOOLS.parent


def parse_time(text):
    try:
        return dt.datetime.strptime(text, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc).timestamp()
    except (TypeError, ValueError):
        return None


def releases(root):
    out = []
    base = Path(root) / flow.QUEUES
    for qdir in sorted(base.iterdir()) if base.is_dir() else []:
        path = qdir / 'releases.jsonl'
        if path.is_file():
            out += [dict(json.loads(l), profile=json.loads(l).get('profile') or flow.QUEUE_PROFILE.get(qdir.name, qdir.name))
                    for l in path.read_text().splitlines() if l.strip()]
    return out


def normalise(text):
    """A failure message with numbers and hex folded, so repeats of one kind count together."""
    text = re.sub(r'0x[0-9a-fA-F]+', '0x_', str(text))
    text = re.sub(r'\d+', 'N', text)
    return ' '.join(text.split())[:120]


def summarise(root, now=None):
    root = Path(root)
    now = time.time() if now is None else now
    recs = flow.queue_results(root)
    table = {'model': defaultdict(lambda: defaultdict(list)), 'profile': defaultdict(lambda: defaultdict(list)), 'tier': defaultdict(lambda: defaultdict(list))}
    messages = Counter()
    for r in recs:
        keys = (('model', wq.model_of(r.get('worker')) + ('/' + r.get('tier') if r.get('tier', 'first') != 'first' else '')), ('profile', (r.get('profile') or 'unrecorded') + ('/' + r.get('tier') if r.get('tier', 'first') != 'first' else '')),
                ('tier', r.get('tier', 'first')))
        for kind, key in keys:
            s = table[kind][key]
            if 'rva' in r:
                s['functions'].append(r)
            elif 'unit' in r or 'task' in r:
                s['units'].append(r)
        if 'rva' in r and r.get('result') != 'pass':
            messages[f'fail: {normalise(r.get("reason") or "no reason")}'] += 1
        for field in ('blocker', 'friction'):
            v = r.get(field)
            for item in (v if isinstance(v, list) else [v]):
                if item:
                    messages[f'{field}: {normalise(item)}'] += 1
    rel = releases(root)
    stalls = []
    for qdir, profile, u, state, who, claim in flow.queue_units(root):
        if state in ('claimed', 'stale'):
            age = now - float((claim or {}).get('time', now))
            if age >= flow.CLAIM_LOOK_SECONDS:
                stalls.append({'unit': u['dir'], 'worker': who, 'profile': profile, 'tier': 'first', 'minutes': int(age // 60)})
        for tier in ('fallback', 'strong'):
            claim = wq.read_claim(wq.tier_dir(qdir, 'claims', tier) / f'{u["key"]}.lock')
            if claim:
                age = now - float(claim.get('time', now))
                if age >= flow.CLAIM_LOOK_SECONDS:
                    stalls.append({'unit': u['dir'], 'worker': claim.get('worker'),
                                   'profile': claim.get('profile') or profile, 'tier': tier, 'minutes': int(age // 60)})
    rows = {}
    for kind, groups in table.items():
        rows[kind] = {}
        for key, s in sorted(groups.items()):
            fns = s['functions']
            passed = [r for r in fns if r.get('result') == 'pass']
            by_unit = defaultdict(list)
            for r in fns:
                by_unit[r.get('queue_unit')].append(r)
            abandoned = sum(1 for rs in by_unit.values() if not any(r.get('result') == 'pass' for r in rs))
            abandoned += sum(1 for r in rel if (wq.model_of(r.get('worker')) + ('/' + r.get('tier') if r.get('tier', 'first') != 'first' else '') if kind == 'model' else (r.get('tier', 'first') if kind == 'tier' else (r.get('profile') or 'unrecorded') + ('/' + r.get('tier') if r.get('tier', 'first') != 'first' else ''))) == key)
            walls = []
            for r in s['units']:
                a, b = parse_time(r.get('claimed')), parse_time(r.get('recorded'))
                if a is not None and b is not None and b >= a:
                    walls.append((b - a) / 60)
            rows[kind][key] = {
                'functions': len(fns), 'passed': len(passed),
                'pass_rate': round(len(passed) / len(fns), 3) if fns else None,
                'attempts_per_pass': round(sum(int(r.get('attempts') or 0) for r in fns) / len(passed), 2) if passed else None,
                'units': len(s['units']), 'abandoned_units': abandoned,
                'stalls_now': sum(1 for st in stalls if (wq.model_of(st['worker']) + ('/' + st['tier'] if st['tier'] != 'first' else '') if kind == 'model' else (st['tier'] if kind == 'tier' else st['profile'] + ('/' + st['tier'] if st['tier'] != 'first' else ''))) == key),
                'median_minutes_per_unit': round(statistics.median(walls), 1) if walls else None,
            }
    rejects = Counter()
    for path in sorted((root / flow.REVIEWS).glob('*.md')) if (root / flow.REVIEWS).is_dir() else []:
        try:
            _, header, blocks = af.review_blocks(path.read_text(encoding='utf-8'))
        except (UnicodeDecodeError, OSError):
            continue
        for parts, body in blocks:
            if body.get('verdict') != 'reject':
                continue
            for check, value in (body.get('_checks') or {}).items():
                if value.startswith('fail'):
                    rejects[f'check {check} failed'] += 1
            for item in body.get('_blocking_findings') or []:
                rejects[normalise(item)] += 1
    cheap = rows['profile'].get('cheap', {})
    flag = None
    if cheap.get('pass_rate') is not None and cheap['pass_rate'] < profiles.CHEAP_MIN_PASS_RATE:
        flag = (f'cheap pass rate {cheap["pass_rate"]} is below {profiles.CHEAP_MIN_PASS_RATE}: '
                'a direction check should consider making `full` the default again')
    return {'generated': flow.utc(), 'by_model': rows['model'], 'by_profile': rows['profile'], 'by_tier': rows['tier'], 'stalls': stalls,
            'releases': len(rel), 'rejects_by_reason': rejects.most_common(15),
            'top_failure_messages': messages.most_common(15), 'default_profile': profiles.DEFAULT,
            'cheap_threshold': profiles.CHEAP_MIN_PASS_RATE, 'cheap_flag': flag}


def render(rep):
    out = [f'# Friction report {rep["generated"]}', '',
           f'Default profile: `{rep["default_profile"]}`; cheap pass-rate threshold {rep["cheap_threshold"]}. '
           + (f'**{rep["cheap_flag"]}**' if rep['cheap_flag'] else 'Cheap profile at or above the threshold (or no data).'), '']
    cols = ('functions', 'passed', 'pass_rate', 'attempts_per_pass', 'units', 'abandoned_units', 'stalls_now',
            'median_minutes_per_unit')
    for title, key in (('By tier', 'by_tier'), ('By profile', 'by_profile'), ('By model', 'by_model')):
        out += [f'## {title}', '', '| key | ' + ' | '.join(cols) + ' |', '|---' * (len(cols) + 1) + '|']
        for k, row in rep[key].items():
            out.append(f'| {k} | ' + ' | '.join('-' if row[c] is None else str(row[c]) for c in cols) + ' |')
        out.append('')
    out += ['## Stalls now', ''] + ([f'- {s["unit"]}: {s["worker"]} ({s["profile"]}), {s["minutes"]} min'
                                     for s in rep['stalls']] or ['none']) + ['']
    out += [f'Released claims (all time): {rep["releases"]}', '']
    out += ['## Rejects by reason', ''] + ([f'- {n} x {r}' for r, n in rep['rejects_by_reason']] or ['none']) + ['']
    out += ['## Top failure messages', ''] + ([f'- {n} x {m}' for m, n in rep['top_failure_messages']] or ['none'])
    return '\n'.join(out) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    p.add_argument('--flow-dir')
    p.add_argument('--write', action='store_true')
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    rep = summarise(a.root)
    text = json.dumps(rep, indent=2) if a.json else render(rep)
    print(text, end='' if text.endswith('\n') else '\n')
    if a.write:
        fdir = flow.flow_dir(a.root, a.flow_dir)
        fdir.mkdir(parents=True, exist_ok=True)
        path = fdir / f'friction-{rep["generated"].replace(":", "").replace("-", "")}.md'
        path.write_text(render(rep))
        flow.log_event(fdir, 'friction', file=str(path), cheap_flag=rep['cheap_flag'])
        print(f'written {path}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
