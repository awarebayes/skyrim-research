"""Small Python wrapper over the Boat CLI for the verifier commands (attempt, confirm).

Same rules as boat_lib.sh: machines are found by name (no account-specific id in the
repository), the CLI never auto-updates under a running command, and nothing here buys, shares
or saves snapshots. BOAT_CLI overrides the CLI path, BOAT_VERIFIER_NAME the standing machine.
"""
from datetime import datetime, timezone
import json
import os
import subprocess

BOAT = os.environ.get('BOAT_CLI', 'boat')
STANDING = os.environ.get('BOAT_VERIFIER_NAME', 'sr-verifier-msvc141')
RUNNING = {'ready', 'idle', 'running'}
REMOTE_HOME = '/home/user'


class BoatError(Exception):
    pass


def _env():
    env = dict(os.environ)
    env['BOAT_NO_UPDATE'] = '1'
    # macOS tar would otherwise add AppleDouble files that make scp uploads fail.
    env['COPYFILE_DISABLE'] = '1'
    return env


def cli(*args, timeout=None, check=True):
    proc = subprocess.run([BOAT, *args], capture_output=True, text=True, env=_env(), timeout=timeout)
    if check and proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
        raise BoatError(f'boat {args[0]} failed (exit {proc.returncode}): {" | ".join(tail)}')
    return proc


def _json_lines(text):
    out = []
    for line in text.splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def lookup(name=STANDING):
    """(id, state) of the machine with this name, or (None, 'missing'); refuses ambiguous names."""
    rows = [s for s in json.loads(cli('list', '--all', '--json').stdout)['sandboxes'] if s.get('name') == name]
    if len(rows) > 1:
        raise BoatError(f'more than one sandbox is named {name!r}; rename the extra one')
    return (rows[0]['id'], rows[0]['state']) if rows else (None, 'missing')


def info(machine):
    return json.loads(cli('info', machine, '--json').stdout)['sandbox']


def seconds_left(sandbox):
    """Seconds until the auto-stop deadline, or None if the machine has none."""
    value = sandbox.get('archiveAfter')
    if not value:
        return None
    when = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return int((when - datetime.now(timezone.utc)).total_seconds())


def _take_start(reason, machine, force):
    # Every start goes through the shared budget check and log (starts.py).
    import starts
    try:
        starts.take(reason, machine, force=force or None, cli=cli)
    except starts.StartsRefused as exc:
        raise BoatError(str(exc)) from None


def resume(machine, ttl, reason='resume', force=False):
    _take_start(reason, machine, force)
    cli('resume', machine, '--ttl', str(ttl), '--json', timeout=300)


def extend(machine, ttl):
    cli('extend', machine, '--ttl', str(ttl), '--json', timeout=60)


def stop(machine):
    cli('stop', machine, '--json', timeout=120)


def delete(machine):
    cli('delete', machine, '--yes', '--json', timeout=120)


def fork(source, name, ttl, reason='fork', force=False):
    _take_start(reason, name, force)
    proc = cli('fork', source, '--no-env', '--no-monitoring', '--ttl', str(ttl), '--wait', '--json', timeout=600)
    found = None
    for event in _json_lines(proc.stdout):
        if event.get('id') and (event.get('event') == 'ready' or event.get('state') == 'ready'):
            found = event['id']
    if found is None:
        ids = {e.get('id') for e in _json_lines(proc.stdout) if e.get('id')}
        raise BoatError(f'fork did not report a ready machine (created: {", ".join(sorted(ids)) or "none"})')
    cli('rename', found, name, check=False)
    return found


def execute(machine, command, timeout):
    """Run a shell command line; returns (exit code, stdout, stderr). Exit 124 on timeout."""
    proc = cli('exec', machine, '--timeout', str(timeout), '--json', '--', command,
               timeout=timeout + 60, check=False)
    try:
        result = json.loads(proc.stdout)
    except ValueError:
        raise BoatError(f'boat exec gave no result: {(proc.stderr or proc.stdout).strip()[-300:]}') from None
    if 'error' in result and 'exitCode' not in result:
        raise BoatError(f'boat exec: {result["error"]}')
    if result.get('timedOut'):
        return 124, result.get('stdout', ''), result.get('stderr', '')
    code = result.get('exitCode')
    return (1 if code is None else code), result.get('stdout', ''), result.get('stderr', '')


def upload(machine, local, remote):
    """Copy a local file or directory to a remote path that must not exist yet."""
    args = ['scp'] + (['-r'] if os.path.isdir(local) else []) + [str(local), f'{machine}:{remote}']
    cli(*args, timeout=900)


def download(machine, remote, local):
    cli('scp', '-r', f'{machine}:{remote}', str(local), timeout=900)


def usage_seconds(machine):
    return json.loads(cli('usage', machine, '--json').stdout).get('seconds')


def compute_used():
    d = json.loads(cli('limits', '--json').stdout)
    return {'trialComputeUsedSeconds': d.get('trialComputeUsedSeconds'),
            'creditUsedSeconds': d.get('creditUsedSeconds'), 'activeSandboxes': d.get('activeSandboxes'),
            'maxActiveSandboxes': d.get('maxActiveSandboxes')}
