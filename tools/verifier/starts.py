#!/usr/bin/env python3
"""Machine-start accounting for every verifier tool that can start a Boat machine.

Boat limits STARTS per rolling minute, hour and day; create, fork and resume each count as one
(docs.boat.dev/limits; measurements in docs/boat-agent-guidelines.md). A tool calls `take()`
right before the CLI call that may start a machine. It reads `boat limits --json`, refuses when
the start would leave fewer than the reserve for the rest of the day or when the hour or minute
window is full, and appends the start with its reason to `<state>/starts.jsonl`.

    python3 tools/verifier/starts.py status
    python3 tools/verifier/starts.py take --reason '<why>' [--machine <name>] [--force]

Settings (environment): SR_STARTS_RESERVE (default 10) starts kept for the rest of the day;
SR_STARTS_FORCE=1 overrides the reserve (never the hour or minute window, which Boat enforces
itself, and never by buying extra starts); SR_VERIFIER_STATE the private state directory
(default: `.local/verifier` of the main checkout, so every worktree shares one log).
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

DEFAULT_RESERVE = 10


class StartsRefused(Exception):
    pass


def state_dir():
    configured = os.environ.get('SR_VERIFIER_STATE')
    if configured:
        return Path(configured)
    here = Path(__file__).resolve().parents[2]
    out = subprocess.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], cwd=here,
                         capture_output=True, text=True)
    root = Path(out.stdout.strip()).parent if out.returncode == 0 and out.stdout.strip() else here
    return root / '.local' / 'verifier'


def reserve_default():
    try:
        return int(os.environ.get('SR_STARTS_RESERVE', DEFAULT_RESERVE))
    except ValueError:
        return DEFAULT_RESERVE


def parse(limits):
    """The start counters of a `boat limits --json` document as {window: {limit, used, remaining}}."""
    starts = limits.get('starts') or {}
    out = {}
    for window in ('minute', 'hour', 'day'):
        w = starts.get(window) or {}
        limit, used = w.get('limit'), w.get('used')
        remaining = w.get('remaining')
        if remaining is None and limit is not None and used is not None:
            remaining = limit - used
        out[window] = {'limit': limit, 'used': used, 'remaining': remaining}
    out['unlimited'] = bool(starts.get('unlimited'))
    out['plan'] = limits.get('sandboxPlanKey') or limits.get('accessTier')
    out['active'] = limits.get('activeSandboxes')
    out['max_active'] = limits.get('maxActiveSandboxes')
    return out


def read_limits(cli=None):
    if cli is None:
        import boatctl
        cli = boatctl.cli
    return json.loads(cli('limits', '--json').stdout)


def line(counters):
    """One printable budget line."""
    d, h, m = counters['day'], counters['hour'], counters['minute']
    return (f'starts: day {d["used"]}/{d["limit"]} used ({d["remaining"]} left), hour {h["used"]}/{h["limit"]} '
            f'({h["remaining"]} left), minute {m["remaining"]}/{m["limit"]} left; plan {counters["plan"]}; '
            f'machines active {counters["active"]}/{counters["max_active"]}')


def check(counters, count=1, reserve=None, force=False):
    """None if `count` starts may go ahead, else the reason they may not."""
    if counters['unlimited'] or count <= 0:
        return None
    reserve = reserve_default() if reserve is None else reserve
    for window in ('minute', 'hour'):
        left = counters[window]['remaining']
        if left is not None and left < count:
            return f'only {left} start(s) left this {window}; wait for the rolling window (never buy extra starts)'
    left = counters['day']['remaining']
    if left is not None and left - count < reserve and not force:
        return (f'{count} start(s) would leave {left - count} for the rest of the day, below the reserve of '
                f'{reserve} (--force or SR_STARTS_FORCE=1 to use the reserve)')
    return None


def log(reason, machine, counters, path=None):
    path = Path(path) if path else state_dir() / 'starts.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {'at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'reason': reason,
             'machine': machine, 'day_used_before': counters['day']['used'],
             'hour_used_before': counters['hour']['used'], 'session': os.environ.get('SR_SESSION_ID')}
    with path.open('a') as f:
        f.write(json.dumps(entry, sort_keys=True) + '\n')
    return entry


def take(reason, machine=None, count=1, reserve=None, force=None, cli=None, say=None):
    """Check the budget for a start that is about to happen and log it; raises StartsRefused."""
    force = os.environ.get('SR_STARTS_FORCE') == '1' if force is None else force
    counters = parse(read_limits(cli))
    if say:
        say(line(counters))
    why = check(counters, count, reserve, force)
    if why:
        raise StartsRefused(f'not starting {machine or "a machine"} ({reason}): {why}')
    log(reason, machine, counters)
    return counters


def logged(path=None, since=None):
    path = Path(path) if path else state_dir() / 'starts.jsonl'
    if not path.is_file():
        return []
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    return [r for r in rows if since is None or r['at'] >= since]


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status')
    t = sub.add_parser('take')
    t.add_argument('--reason', required=True)
    t.add_argument('--machine')
    t.add_argument('--reserve', type=int)
    t.add_argument('--force', action='store_true')
    a = p.parse_args()
    try:
        if a.cmd == 'status':
            print(line(parse(read_limits())))
            return 0
        take(a.reason, a.machine, reserve=a.reserve, force=a.force or None, say=lambda s: print(s, file=sys.stderr))
        return 0
    except StartsRefused as exc:
        print(f'starts: {exc}', file=sys.stderr)
        return 5


if __name__ == '__main__':
    raise SystemExit(main())
