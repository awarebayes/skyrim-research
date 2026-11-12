"""Verifier session: two long-lived, separately installed verifier machines for one work period.

Machine A is the standing verifier (`sr-verifier-msvc141`), machine B a second verifier built
from the same recipe by its own run of setup_boat_machine.sh (not a disk fork), so a pair of
runs on A and B checks the toolchain install as well as the process. A session costs at most one
start per machine; `attempt` and `confirm` then run on the machines without starting or stopping
anything. The command line is tools/verifier/session; this module is shared with attempt,
confirm and pipeline.

Private state lives in starts.state_dir() (default `.local/verifier/` of the main checkout):
`session.json` (machine ids, deadlines, counters at `up`), `session-attributed.jsonl` (seconds
attempt/confirm already queued for the cost ledger during the session) and `sessions.jsonl`
(one summary per finished session).
"""
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

import boatctl
import starts

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NAMES = {'a': boatctl.STANDING, 'b': os.environ.get('BOAT_VERIFIER_B_NAME', 'sr-verifier-b')}
LABELS = {'a': 'boat-verifier-a', 'b': 'boat-verifier-b'}
DEFAULT_TTL = int(os.environ.get('SR_SESSION_TTL', '3600'))
# Trial accounts refuse an auto-stop above this; paid plans allow more but sessions stay bounded.
MAX_TTL = 7200
# Extend a session machine when less than this remains, so no unit races the auto-stop.
MIN_LEFT = 900
# A stopped disk is kept at least 14 days; warn early enough for a resume/stop cycle.
RETENTION_WARN_DAYS = 10
STARTING = {'provisioning', 'provisioned', 'starting', 'cloning'}


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def session_path():
    return starts.state_dir() / 'session.json'


def load():
    try:
        return json.loads(session_path().read_text())
    except (OSError, ValueError):
        return None


def save(session):
    path = session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(session, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def active():
    s = load()
    return s if s and s.get('state') == 'up' else None


def note_attributed(seconds, task_id, stage):
    """Remember seconds a verifier command queued for the ledger, so `down` books only the rest."""
    if not active() or seconds is None:
        return
    try:
        path = starts.state_dir() / 'session-attributed.jsonl'
        with path.open('a') as f:
            f.write(json.dumps({'at': now_iso(), 'seconds': round(float(seconds), 3), 'task': task_id,
                                'stage': stage}) + '\n')
    except OSError:
        pass


def attributed_since(since):
    path = starts.state_dir() / 'session-attributed.jsonl'
    if not path.is_file():
        return 0.0
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    return sum(r['seconds'] for r in rows if r['at'] >= since)


def _parse_time(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None


def last_stop(sandbox):
    stop = sandbox.get('stop') or {}
    return _parse_time(sandbox.get('stoppedAt') or stop.get('endedAt'))


def wait_state(machine, wanted, limit=300):
    end = time.monotonic() + limit
    while time.monotonic() < end:
        state = boatctl.info(machine)['state']
        if state in wanted:
            return state
        time.sleep(2)
    raise boatctl.BoatError(f'machine {machine} did not reach {"/".join(sorted(wanted))} in {limit}s')


def markers(machine):
    """Task ids with a `.running` marker on a running machine."""
    code, out, _ = boatctl.execute(machine, f'ls -d {boatctl.REMOTE_HOME}/tasks/*/.running 2>/dev/null || true', 60)
    return [p.split('/')[-2] for p in out.split()] if code == 0 else ['<marker check failed>']


def verify_script(build_id):
    """Shell line printing TOOLCHAIN=ok|bad and IMAGE=<sha256>|missing; reads no repository files."""
    pin = (HERE / 'pinned.sha256').read_text()
    blob = base64.b64encode(pin.encode()).decode()
    image = f'{boatctl.REMOTE_HOME}/private/{build_id}/SkyrimSE.exe'
    lines = [
        f'cd {boatctl.REMOTE_HOME}/msvc/VC/Tools/MSVC/*/bin/Hostx64/x64 2>/dev/null '
        f'&& printf %s {blob} | base64 -d | sha256sum -c --quiet - >/dev/null 2>&1 '
        '&& echo TOOLCHAIN=ok || echo TOOLCHAIN=bad',
        f'f={shlex.quote(image)}; if [ -f "$f" ]; then echo IMAGE=$(sha256sum "$f" | cut -d" " -f1); '
        'else echo IMAGE=missing; fi',
        'echo CPUS=$(nproc)',
    ]
    return 'bash -c ' + shlex.quote('\n'.join(lines))


def verify(machine, target, local_image=None, upload=None):
    """{'toolchain': ok|bad, 'image': ok|missing|mismatch, 'cpus': n}; uploads a missing image once."""
    def probe():
        code, out, _ = boatctl.execute(machine, verify_script(target['build_id']), 600)
        fields = dict(line.split('=', 1) for line in out.splitlines() if '=' in line)
        if code != 0 or 'TOOLCHAIN' not in fields:
            raise boatctl.BoatError(f'hash check on {machine} gave no result (exit {code})')
        return fields
    fields = probe()
    if fields.get('IMAGE') == 'missing' and upload is not None and local_image:
        upload(machine)
        fields = probe()
    image = fields.get('IMAGE')
    return {'toolchain': 'ok' if fields.get('TOOLCHAIN') == 'ok' else 'bad',
            'image': 'missing' if image == 'missing' else ('ok' if image == target['image_sha256'] else 'mismatch'),
            'cpus': int(fields['CPUS']) if fields.get('CPUS', '').isdigit() else None}


def upload_image(machine, build_id, local_image):
    dest = f'{boatctl.REMOTE_HOME}/private/{build_id}/SkyrimSE.exe'
    parent = str(Path(dest).parent)
    boatctl.execute(machine, f'mkdir -p -m 700 {shlex.quote(parent)} && rm -f {shlex.quote(dest)}.part', 60)
    boatctl.upload(machine, local_image, dest + '.part')
    code, _, _ = boatctl.execute(machine, f'chmod 600 {shlex.quote(dest)}.part && mv {shlex.quote(dest)}.part '
                                 f'{shlex.quote(dest)}', 60)
    if code != 0:
        raise boatctl.BoatError(f'cannot place the image on {machine}')


def local_image():
    path = starts.state_dir() / 'config.json'
    for candidate in (path, REPO / '.local' / 'verifier' / 'config.json'):
        try:
            return json.loads(candidate.read_text()).get('image')
        except (OSError, ValueError):
            continue
    return None


def compute_counters():
    d = json.loads(boatctl.cli('limits', '--json').stdout)
    return d, {'creditUsedSeconds': d.get('creditUsedSeconds'),
               'trialComputeUsedSeconds': d.get('trialComputeUsedSeconds')}


def create(name, ttl, force, log):
    """Build a machine from the recipe through boat_up.sh's create path (one start, several minutes)."""
    env = dict(os.environ, BOAT_VERIFIER_NAME=name, BOAT_ALLOW_CREATE='1', BOAT_TTL=str(ttl))
    if force:
        env['SR_STARTS_FORCE'] = '1'
    log(f'{name}: creating from the recipe (setup_boat_machine.sh; about 7 minutes)')
    proc = subprocess.run([str(HERE / 'boat_up.sh')], env=env, capture_output=True, text=True)
    tail = (proc.stderr or '').strip().splitlines()[-3:]
    if proc.returncode != 0:
        raise boatctl.BoatError(f'{name}: create failed (exit {proc.returncode}): {" | ".join(tail)}')
    machine, _ = boatctl.lookup(name)
    if machine is None:
        raise boatctl.BoatError(f'{name}: boat_up.sh finished but no machine has that name')
    return machine


def up(ttl=DEFAULT_TTL, reserve=None, force=False, allow_create=False, only=None, log=print):
    """Resume, reuse or (with allow_create) build A and B; at most one start per machine."""
    if ttl > MAX_TTL:
        raise boatctl.BoatError(f'ttl {ttl} is above {MAX_TTL}; use `session extend` later instead')
    keys = [only] if only else ['a', 'b']
    target = json.loads((REPO / 'builds/target.json').read_text())
    limits, compute = compute_counters()
    counters = starts.parse(limits)
    log(starts.line(counters))
    found = {}
    for key in keys:
        machine, state = boatctl.lookup(NAMES[key])
        if state == 'missing' and key == 'a':
            raise boatctl.BoatError(f'no machine named {NAMES["a"]}; rebuilding A is lifecycle rule 3 of '
                                    'docs/boat-agent-guidelines.md, not part of `session up`')
        if state == 'missing' and not allow_create:
            raise boatctl.BoatError(f'no machine named {NAMES[key]}; `session up --create` builds it from the '
                                    'recipe (one start, about 7 minutes, accepts the Build Tools licence)')
        found[key] = (machine, state)
    needed = sum(1 for _, state in found.values() if state not in boatctl.RUNNING | STARTING)
    why = starts.check(counters, needed, reserve, force)
    if why:
        raise starts.StartsRefused(f'session up needs {needed} start(s): {why}')

    session = active() or {'schema': 1, 'state': 'up', 'started_at': now_iso(), 'machines': {},
                           'compute_at_up': compute, 'starts_at_up': counters['day'],
                           'attributed_consumed': 0.0}
    session['state'] = 'up'
    os.environ['SR_SESSION_ID'] = session['started_at']
    for key in keys:
        name = NAMES[key]
        machine, state = found[key]
        if state == 'missing':
            machine = create(name, ttl, force, log)
            how = 'created from the recipe'
        elif state in boatctl.RUNNING:
            left = boatctl.seconds_left(boatctl.info(machine))
            if left is not None and left < MIN_LEFT:
                boatctl.extend(machine, ttl)
                how = f'already running; deadline extended to {ttl // 60} min'
            else:
                how = 'already running; deadline left as it was' + (f' ({left // 60} min)' if left else '')
        elif state in STARTING:
            wait_state(machine, boatctl.RUNNING)
            how = 'was starting; now running'
        else:
            if state == 'stopping':
                wait_state(machine, {'stopped'})
            boatctl.resume(machine, ttl, reason=f'session up {key}', force=force)
            how = f'resumed, auto-stop in {ttl // 60} min'
        log(f'{key.upper()} {name}: {how}')
        prior = session['machines'].get(key) or {}
        session['machines'][key] = {'name': name, 'id': machine, 'how': how, 'state': 'up',
                                    'usage_at_up': prior.get('usage_at_up', boatctl.usage_seconds(machine)),
                                    'up_at': prior.get('up_at', now_iso())}
    image = local_image()

    def check_one(key):
        machine = session['machines'][key]['id']
        return key, verify(machine, target, image, lambda m: upload_image(m, target['build_id'], image))
    with ThreadPoolExecutor(max_workers=len(keys)) as pool:
        results = dict(pool.map(check_one, keys))
    bad = []
    for key, result in results.items():
        entry = session['machines'][key]
        entry.update({'toolchain': result['toolchain'], 'image': result['image'], 'cpus': result['cpus']})
        entry['deadline'] = boatctl.info(entry['id']).get('archiveAfter')
        log(f'{key.upper()} {entry["name"]}: toolchain {result["toolchain"]} (pinned.sha256), image '
            f'{result["image"]} (builds/target.json), {result["cpus"]} CPUs, auto-stop at {entry["deadline"]}')
        if result['toolchain'] != 'ok' or result['image'] != 'ok':
            bad.append(key)
            entry['state'] = 'unverified'
    save(session)
    if bad:
        raise boatctl.BoatError(f'machine(s) {", ".join(k.upper() for k in bad)} failed the hash checks; do not '
                                'verify on them (left running for inspection; `session down` stops them)')
    log(starts.line(starts.parse(compute_counters()[0])))
    return session


def hosts(min_left=MIN_LEFT, ttl=DEFAULT_TTL):
    """[(key, label, machine id)] of a session's A and B, both running; never starts a machine."""
    session = active()
    if session is None:
        return None
    out = []
    for key in ('a', 'b'):
        entry = (session.get('machines') or {}).get(key)
        if not entry or entry.get('state') != 'up':
            raise boatctl.BoatError(f'verifier session has no verified machine {key.upper()}; '
                                    'an Engineer runs `tools/verifier/session up`')
        machine, state = boatctl.lookup(entry['name'])
        if machine != entry['id'] or state not in boatctl.RUNNING:
            raise boatctl.BoatError(f'session machine {key.upper()} ({entry["name"]}) is {state}; nothing is '
                                    'started from here: an Engineer runs `tools/verifier/session up`')
        left = boatctl.seconds_left(boatctl.info(machine))
        if left is not None and left < min_left:
            boatctl.extend(machine, ttl)
        out.append((key, LABELS[key], machine))
    return out


def machine_for_attempt(ttl=DEFAULT_TTL):
    """(id, how) of A when a session is up, else None; never starts or stops a machine."""
    session = active()
    if session is None:
        return None
    entry = (session.get('machines') or {}).get('a')
    if not entry:
        raise boatctl.BoatError('verifier session has no machine A; an Engineer runs `tools/verifier/session up`')
    machine, state = boatctl.lookup(entry['name'])
    if state not in boatctl.RUNNING:
        raise boatctl.BoatError(f'verifier session is up but {entry["name"]} is {state}; attempts never start it: '
                                'an Engineer runs `tools/verifier/session up`')
    left = boatctl.seconds_left(boatctl.info(machine))
    if left is not None and left < MIN_LEFT:
        boatctl.extend(machine, ttl)
        return machine, f'session A, deadline extended to {ttl // 60} min'
    return machine, 'session A' + (f', auto-stop in {left // 60} min' if left is not None else '')


def status(log=print):
    """Print machines, deadlines, task markers, retention, starts and session compute; returns warnings."""
    session = load() or {}
    limits, compute = compute_counters()
    counters = starts.parse(limits)
    warnings = []
    log(f'session: {session.get("state", "none")}' + (f' since {session["started_at"]}' if session.get('started_at') else ''))
    rows = {s.get('name'): s for s in json.loads(boatctl.cli('list', '--all', '--json').stdout)['sandboxes']}
    used = 0
    for key in ('a', 'b'):
        name = NAMES[key]
        s = rows.get(name)
        if s is None:
            log(f'{key.upper()} {name}: missing')
            continue
        sandbox = boatctl.info(s['id'])
        state = sandbox['state']
        parts = [f'{key.upper()} {name}: {state}']
        if state in boatctl.RUNNING:
            left = boatctl.seconds_left(sandbox)
            parts.append('no auto-stop' if left is None else f'auto-stop in {left // 60} min {left % 60} s')
            busy = markers(s['id'])
            parts.append('tasks running: ' + (' '.join(busy) if busy else 'none'))
        else:
            stopped = last_stop(sandbox)
            if stopped is not None:
                days = (datetime.now(timezone.utc) - stopped).total_seconds() / 86400
                parts.append(f'stopped {days:.1f} days ago')
                if days >= RETENTION_WARN_DAYS:
                    warnings.append(f'{name} has been stopped {days:.0f} days; the disk is kept at least 14 days '
                                    'after a stop: resume and stop it (`session up --only '
                                    f'{key}` then `session down --only {key}`) before day 14')
        entry = (session.get('machines') or {}).get(key)
        if entry and entry.get('id') == s['id'] and entry.get('usage_at_up') is not None:
            delta = boatctl.usage_seconds(s['id']) - entry['usage_at_up']
            used += delta
            parts.append(f'{delta} s billed this session')
        log('; '.join(parts))
    log(starts.line(counters))
    if session.get('started_at'):
        made = starts.logged(since=session['started_at'])
        log(f'this session: {len(made)} start(s) by these tools, {used} s machine time on A and B')
    log(f'compute: creditUsedSeconds={compute["creditUsedSeconds"]} '
        f'trialComputeUsedSeconds={compute["trialComputeUsedSeconds"]}')
    for w in warnings:
        log(f'WARNING: {w}')
    return warnings


def extend(ttl=DEFAULT_TTL, log=print):
    """Push the deadline of each running session machine to now + ttl; never shortens one."""
    if ttl > MAX_TTL:
        raise boatctl.BoatError(f'ttl {ttl} is above {MAX_TTL}')
    session = active()
    if session is None:
        raise boatctl.BoatError('no verifier session is up')
    for key, entry in sorted(session['machines'].items()):
        machine, state = boatctl.lookup(entry['name'])
        if state not in boatctl.RUNNING:
            log(f'{key.upper()} {entry["name"]}: {state}, not extended (extend never starts a machine)')
            continue
        left = boatctl.seconds_left(boatctl.info(machine))
        if left is not None and left >= ttl:
            log(f'{key.upper()} {entry["name"]}: {left // 60} min left, more than requested; unchanged')
            continue
        boatctl.extend(machine, ttl)
        entry['deadline'] = boatctl.info(machine).get('archiveAfter')
        log(f'{key.upper()} {entry["name"]}: auto-stop at {entry["deadline"]}')
    save(session)


def down(only=None, force=False, log=print, record=None):
    """Stop the session's machines (or one); refuses while task markers exist unless force."""
    session = load()
    if session is None:
        raise boatctl.BoatError('no verifier session file; `session status` shows the machines')
    keys = [only] if only else sorted(session['machines'])
    machines = {}
    for key in keys:
        entry = session['machines'].get(key)
        if entry is None:
            raise boatctl.BoatError(f'machine {key.upper()} is not part of this session')
        machine, state = boatctl.lookup(entry['name'])
        if machine != entry['id']:
            raise boatctl.BoatError(f'{entry["name"]} is not the machine this session brought up; stop it by hand')
        machines[key] = (machine, state)
    busy = {k: markers(m) for k, (m, st) in machines.items() if st in boatctl.RUNNING}
    busy = {k: v for k, v in busy.items() if v}
    if busy and not force:
        raise SessionBusy('not stopping: tasks marked running: ' + '; '.join(
            f'{k.upper()}: {" ".join(v)}' for k, v in busy.items()) + ' (--force only for markers known to be stale)')
    seconds = 0
    for key, (machine, state) in machines.items():
        if state not in {'stopped'}:
            if state != 'stopping':
                boatctl.stop(machine)
            wait_state(machine, {'stopped'})
        entry = session['machines'][key]
        delta = boatctl.usage_seconds(machine) - (entry.get('usage_at_up') or 0)
        entry.update({'state': 'down', 'down_at': now_iso(), 'seconds': delta})
        seconds += delta
        log(f'{key.upper()} {entry["name"]}: stopped; {delta} s billed since session up')
    remaining = [k for k, e in session['machines'].items() if e.get('state') == 'up']
    made = starts.logged(since=session['started_at'])
    attributed = attributed_since(session['started_at']) - session.get('attributed_consumed', 0.0)
    booked = max(0.0, seconds - max(0.0, attributed))
    session['attributed_consumed'] = session.get('attributed_consumed', 0.0) + min(seconds, max(0.0, attributed))
    if record is not None:
        record(booked, len(made) if not remaining else None)
    log(f'cost ledger queue: {booked:.0f} s session overhead (machine time minus {min(seconds, max(attributed, 0)):.0f} s '
        'already queued by attempt/confirm); run `python3 tools/cost_ledger.py flush`')
    log(f'starts made by these tools this session: {len(made)}')
    if remaining:
        log('still up: ' + ', '.join(f'{k.upper()} {session["machines"][k]["name"]}' for k in remaining))
    else:
        session['state'] = 'down'
        session['ended_at'] = now_iso()
        with (starts.state_dir() / 'sessions.jsonl').open('a') as f:
            f.write(json.dumps({'started_at': session['started_at'], 'ended_at': session['ended_at'],
                                'starts': len(made), 'machines': session['machines']}, sort_keys=True) + '\n')
    save(session)
    log(starts.line(starts.parse(compute_counters()[0])))
    return session


class SessionBusy(Exception):
    pass
