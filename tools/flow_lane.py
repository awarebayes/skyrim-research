"""One durable push lane. The live state lock is used only for queue/receipt mutations.

Candidates are independent local clones with private flow snapshots. No branch, stash or
worktree is removed, including failed candidates. A run drains one frozen queue snapshot.
"""
from contextlib import contextmanager
import fcntl
from functools import wraps
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import shlex
import socket
import subprocess
import sys
import time
import uuid

import flow as f
import resource_admission
import check as check_gate
from check_source_digest import source_digest_cache
from flow_state import state_lock, atomic_write, require_complete


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    atomic_write(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def guard_cleanup(fdir, root):
    # Called under the state lock by every enqueue/resume path.
    for reservation in (Path(fdir) / 'cleanup/claims').glob('*.json'):
        claim = read(reservation)
        f.refuse(not claim.get('active') or not Path(root).resolve().is_relative_to(Path(claim['tree'])),
                 'input checkout is being cleaned; retry after cleanup with a retained input')


def enqueue(root, fdir, kind, selection, branch='main', approved_only=False, with_metadata=False, name=None):
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    payload = dict(root=str(root), kind=kind, selection=selection, branch=branch,
                   approved_only=approved_only, with_metadata=with_metadata, name=name)
    key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    path = fdir / 'lane/queue' / (key + '.json')
    with state_lock(fdir):
        require_complete(fdir)
        guard_cleanup(fdir, root)
        if path.exists():
            previous = read(path)
            if previous['state'] in ('queued', 'running'):
                return previous
        item = dict(payload, id=key, state='queued', queued_at=f.utc())
        write(path, item)
    return item


@contextmanager
def lane_lock(fdir, wait=False, purpose=None):
    path = Path(fdir) / 'lane/.lane.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        except BlockingIOError:
            raise f.FlowError('push lane already running; queued work stays for the next run') from None
        owner_path = Path(fdir) / 'lane/owner.json'
        if purpose:
            with state_lock(fdir):
                write(owner_path, dict(process_owner(), kind=purpose, active=True))
        lease = LaneLease(handle, fdir, owner_path, purpose)
        try:
            yield lease
        finally:
            lease.release()


class LaneLease:
    """A build/push lease that may finish before the enclosing CI watch."""
    def __init__(self, handle, fdir, owner_path, purpose):
        self.handle, self.fdir, self.owner_path, self.purpose = handle, fdir, owner_path, purpose
        self.started, self.seconds, self.released = time.monotonic(), None, False

    def release(self):
        if self.released:
            return
        self.seconds = time.monotonic() - self.started
        if self.purpose:
            with state_lock(self.fdir):
                owner = read(self.owner_path)
                owner.update(active=False, hold_seconds=self.seconds)
                write(self.owner_path, owner)
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        self.seconds = time.monotonic() - self.started
        self.released = True


def running(fdir):
    """Probe the permanent lane lock without waiting for a runner."""
    try:
        with lane_lock(fdir):
            return False
    except f.FlowError:
        return True


def snapshot(fdir, destination):
    """Only small scheduling files, never integration trees or analysis inputs."""
    with state_lock(fdir):
        require_complete(fdir)
        destination.mkdir(parents=True, exist_ok=True)
        for name in ('groups', 'imports', 'combined', 'lane/queue', 'lane/runs', 'lane/tooling', 'lane/tooling-queue'):
            if (fdir / name).exists():
                shutil.copytree(fdir / name, destination / name)
        for name in ('versions.json', 'events.jsonl', 'lane/owner.json'):
            if (fdir / name).is_file():
                (destination / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(fdir / name, destination / name)
    write(destination / 'lane-live.json', dict(running=running(fdir), flow_dir=str(Path(fdir).resolve())))


def process_owner():
    return dict(pid=os.getpid(), host=socket.gethostname(), birth=process_birth(os.getpid()))


def process_birth(pid):
    result = subprocess.run(['ps', '-p', str(int(pid)), '-o', 'lstart='], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def owner_alive(owner):
    if not owner:
        return False
    if owner.get('host') != socket.gethostname():
        return True  # An unknown host is not evidence of a dead process.
    birth = process_birth(owner['pid'])
    return bool(birth and birth == owner.get('birth'))


def run_status(root, fdir, receipt, active=None):
    value = dict(receipt)
    live = Path(fdir) / 'lane-live.json'
    info = read(live) if live.is_file() else {}
    actual = info.get('flow_dir', str(fdir))
    prefix = ('python3 ' + shlex.quote(str(f.TOOLS / 'flow.py')) + ' --root ' + shlex.quote(str(receipt.get('root') or root))
              + ' --flow-dir ' + shlex.quote(actual))
    if receipt.get('state') in ('running', 'stale', 'failed', 'conflict'):
        active = (info['running'] if 'running' in info else running(fdir)) if active is None else active
        alive = owner_alive(receipt.get('owner'))
        # Legacy receipts have no PID. A held lane lock protects those old runners.
        owner_path = Path(fdir) / 'lane/owner.json'
        holder = read(owner_path) if owner_path.is_file() else {}
        other_owner = (holder.get('active') and owner_alive(holder)
                       and holder.get('kind') != (receipt.get('kind') or 'integration'))
        stale = not alive and (bool(receipt.get('owner')) or not active or other_owner)
        value['status'] = 'stale' if stale else 'running' if active else 'paused'
        value['lane_busy'] = active
        command = 'tooling-push' if receipt.get('kind') == 'tooling' else 'lane-run'
        value['resume_command'] = prefix + ' ' + command + ' --resume ' + shlex.quote(receipt['id']) + ' --branch ' + shlex.quote(receipt['branch'])
        if not (receipt.get('integrated') or {}).get('pushed'):
            value['retire_command'] = prefix + ' lane-retire ' + receipt['id'] + " --reason 'owner stopped; selection superseded'"
    return value


def receipt_path(fdir, run_id):
    """Resolve an explicit run id across acceptance and tooling receipts, never guess."""
    f.refuse(run_id and Path(run_id).name == run_id and run_id not in ('.', '..'), 'invalid run id')
    paths = [Path(fdir) / 'lane' / kind / (run_id + '.json') for kind in ('runs', 'tooling')]
    found = [p for p in paths if p.is_file()]
    f.refuse(len(found) == 1, 'no unique lane or tooling receipt for ' + run_id)
    return found[0]


def retire(root, fdir, run_id, reason):
    with lane_lock(fdir), state_lock(fdir):
        path = receipt_path(fdir, run_id)
        receipt = read(path)
        f.refuse(receipt['state'] in ('running', 'stale', 'failed', 'conflict'), 'only an unfinished or failed run can be retired')
        f.refuse(not (receipt.get('integrated') or {}).get('pushed'), 'pushed run must resume CI; cannot retire it')
        receipt.update(state='retired', retired_at=f.utc(), retirement_reason=reason)
        for item in receipt.get('items', []):
            item['state'] = 'retired'
        if path.parent.name == 'tooling':
            write(path, receipt)
        else:
            save_run(fdir, receipt)
        f.log_event(Path(fdir), 'lane-retired', lane=run_id, kind=receipt.get('kind', 'integration'), reason=reason)
        return receipt


def lane_python(requested):
    """The worker interpreter is a transport/build prerequisite, never a match predicate."""
    configured = os.environ.get('SKYRIM_LANE_PYTHON')
    candidate = configured or (requested if sys.version_info[:2] == (3, 13) else shutil.which('python3.13'))
    f.refuse(candidate, 'lane requires python3.13 with pyexpat; set SKYRIM_LANE_PYTHON')
    if Path(candidate).resolve() == Path(sys.executable).resolve() and sys.version_info[:2] == (3, 13):
        try:
            import pyexpat
        except ImportError:
            raise f.FlowError('lane requires python3.13 with working pyexpat') from None
        return str(candidate)
    result = subprocess.run([str(candidate), '-c',
                             'import sys,pyexpat; sys.exit(0 if sys.version_info[:2] == (3,13) else 1)'],
                            capture_output=True, text=True)
    f.refuse(result.returncode == 0, 'lane requires python3.13 with working pyexpat; interpreter refused: ' + str(candidate))
    return str(candidate)


def recover_stale(fdir):
    """Skip dead local unpublished owners under the build lease; retain every input and candidate."""
    with state_lock(fdir):
        for directory in ('runs', 'tooling'):
            for path in (Path(fdir) / 'lane' / directory).glob('*.json'):
                receipt = read(path)
                owner = receipt.get('owner') or {}
                if (receipt.get('state') != 'running' or not owner or owner.get('host') != socket.gethostname()
                        or owner_alive(owner) or (receipt.get('integrated') or {}).get('pushed')):
                    continue
                receipt.update(state=('conflict' if 'git rebase' in receipt.get('error', '') else 'stale'), stale_at=f.utc(),
                               recovery_reason='Dead local publisher skipped; inputs and candidate retained')
                for item in receipt.get('items', []):
                    item['state'] = 'stale'
                if directory == 'runs':
                    save_run(fdir, receipt)
                else:
                    write(path, receipt)
                f.log_event(Path(fdir), 'lane-stale-skipped', lane=receipt['id'])


def wait_for_owner(root, fdir, directory, resume, wait):
    """A live other publisher is a queue wait; own/stale work needs an explicit resume."""
    while True:
        with state_lock(fdir):
            unfinished = [read(p) for p in (Path(fdir) / 'lane' / directory).glob('*.json')
                          if read(p)['state'] == 'running'
                          and not (read(p).get('integrated') or {}).get('pushed')]
        blockers = [r for r in unfinished if r['id'] != resume]
        blockers = [r for r in blockers if not (r.get('root') == str(root)
                    and (r.get('owner') or {}).get('pid') == os.getpid() and not running(fdir))]
        if not blockers:
            return
        blockers = [r for r in blockers if owner_alive(r.get('owner'))
                    or (not r.get('owner') and running(fdir))]
        if not blockers:
            return
        for r in blockers:
            command = run_status(root, fdir, r)['resume_command']
            f.refuse(owner_alive(r.get('owner')) or (not r.get('owner') and running(fdir)),
                     'unfinished ' + ('tooling publication' if directory == 'tooling' else 'lane run')
                     + '; resume own or stale receipt: ' + command)
        f.refuse(wait, 'live publisher busy; retry with --wait-lane')
        time.sleep(0.25)


def require_green(root, commit, python, ci_wait):
    result = subprocess.run([python, 'tools/ci_status.py', '--commit', commit, '--wait', str(ci_wait)],
                            cwd=root, capture_output=True, text=True)
    f.refuse(result.returncode == 0, 'origin CI is not green: ' + result.stdout.strip())


def publish_tooling(root, fdir, branch='main', ci_wait=600, python=sys.executable, resume=None, wait_lane=False,
                    soft_free_gb=None, allow_low_disk=False):
    """Check and publish committed tooling under the same lane lock as acceptance work."""
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    python = lane_python(python)
    if resume and receipt_path(fdir, resume).parent.name == 'runs':
        return run_lane(root, fdir, branch, True, ci_wait, python, soft_free_gb=soft_free_gb,
                        allow_low_disk=allow_low_disk, resume=resume, wait_lane=wait_lane)
    if wait_lane and not resume:
        import flow_tooling
        return flow_tooling.publish(root, fdir, branch, ci_wait, python, soft_free_gb, allow_low_disk)
    if resume:
        with state_lock(fdir):
            previous = read(receipt_path(fdir, resume))
        if (previous.get('integrated') or {}).get('pushed'):
            f.refuse(previous['root'] == str(root) and previous['branch'] == branch,
                     'resume tooling publication with its original root and branch')
            return finish_tooling(root, fdir, previous, python, ci_wait)
    wait_for_owner(root, fdir, 'tooling', resume, wait_lane)
    with lane_lock(fdir, wait=wait_lane, purpose='tooling') as lease:
        recover_stale(fdir)
        with state_lock(fdir):
            pending = [read(p) for p in (fdir / 'lane/tooling').glob('*.json') if read(p)['state'] == 'running' and not (read(p).get('integrated') or {}).get('pushed')]
            if resume:
                selected = read(receipt_path(fdir, resume))
                f.refuse(selected['state'] in ('running', 'failed', 'conflict', 'stale'), 'receipt cannot be resumed')
                pending = [selected]
            f.refuse(len(pending) <= 1, 'multiple unfinished tooling publications')
            if pending:
                receipt = pending[0]
                f.refuse(resume == receipt['id'], 'unfinished tooling publication; use tooling-push --resume ' + receipt['id'])
                f.refuse(receipt['root'] == str(root) and receipt['branch'] == branch,
                         'resume tooling publication with its original root and branch')
            else:
                f.refuse(not resume, 'no unfinished tooling publication with that id')
                receipt = dict(id=uuid.uuid4().hex[:16], kind='tooling', root=str(root), branch=branch,
                               state='running', integrated=None)
            guard_cleanup(fdir, root)
            if receipt.get('tree'):
                guard_cleanup(fdir, receipt['tree'])
            receipt['owner'] = process_owner()
            receipt.update(state='running', python=python)
            path = fdir / 'lane/tooling' / (receipt['id'] + '.json')
            write(path, receipt)

        def save():
            with state_lock(fdir):
                write(path, receipt)

        try:
            integ = receipt.get('integrated') or {}
            if not integ.get('pushed'):
                f.refuse(not f.git(root, 'status', '--porcelain', '--untracked-files=all'),
                         'tooling-push requires a clean, committed checkout')
                for attempt in range(3):
                    f.git(root, 'fetch', '--quiet', 'origin', branch)
                    base = f.git(root, 'rev-parse', f'origin/{branch}')
                    checked = receipt.get('integrated') or {}
                    if (checked.get('checks') and checked.get('commit') == f.git(root, 'rev-parse', 'HEAD')
                            and f.git(root, 'merge-base', checked['commit'], base) == checked['commit']):
                        # Recover death after the server accepted the push but before its receipt write.
                        integ = checked
                        integ['pushed'] = f.utc()
                        save()
                        break
                    f.refuse(f.git(root, 'rev-parse', 'HEAD') != base, 'no tooling commit to push')
                    if f.git(root, 'merge-base', base, 'HEAD') != base:
                        f.git(root, 'rebase', f'origin/{branch}')
                    commit = f.git(root, 'rev-parse', 'HEAD')
                    checked = receipt.get('integrated') or {}
                    if not (checked.get('checks') and checked.get('commit') == commit):
                        resource_admission.admit(root, 'tooling validation', soft_gb=soft_free_gb, allow_low_disk=allow_low_disk)
                        started = time.monotonic()
                        logs = fdir / 'lane/tooling' / receipt['id'] / str(len(receipt.get('attempts', [])))
                        receipt['checks_log_dir'] = str(logs)
                        receipt.setdefault('attempts', []).append(dict(commit=commit, base=base, logs=str(logs)))
                        save()
                        f.pre_push_checks(root, commit, python, candidate=True, log_dir=logs)
                        receipt['integrated'] = integ = dict(commit=commit, base_revision=base, checks=f.utc(),
                                                            pushed=None, ci=None, wall_seconds={'checks': time.monotonic()-started})
                        save()
                    else:
                        integ = checked
                        integ['base_revision'] = base
                    # A red main must be resolved before unrelated publication.
                    result = subprocess.run([python, 'tools/ci_status.py', '--commit', base, '--wait', str(ci_wait)],
                                            cwd=root, capture_output=True, text=True)
                    f.refuse(result.returncode == 0, 'origin CI is not green: ' + result.stdout.strip())
                    f.git(root, 'fetch', '--quiet', 'origin', branch)
                    if f.git(root, 'rev-parse', f'origin/{branch}') != base:
                        continue
                    f.refuse(f.git(root, 'rev-parse', 'HEAD') == commit and
                             not f.git(root, 'status', '--porcelain', '--untracked-files=all'), 'checked tooling tree changed')
                    pushed = subprocess.run(['git', 'push', 'origin', f'{commit}:refs/heads/{branch}'],
                                            cwd=root, capture_output=True, text=True)
                    if pushed.returncode:
                        f.git(root, 'fetch', '--quiet', 'origin', branch)
                        f.refuse(f.git(root, 'rev-parse', f'origin/{branch}') != base,
                                 'tooling push failed: ' + pushed.stderr.strip())
                        continue
                    integ['pushed'] = f.utc()
                    save()
                    break
                f.refuse(integ.get('pushed'), 'origin kept moving; resume tooling-push after coordinating publishers')
            lease.release()
            receipt['lane_hold_seconds'] = lease.seconds
            save()
            return finish_tooling(root, fdir, receipt, python, ci_wait)

        except BaseException as error:
            if (receipt.get('integrated') or {}).get('pushed'):
                raise
            receipt['error'] = str(error)
            if 'git rebase' in str(error) and not (receipt.get('integrated') or {}).get('pushed'):
                receipt['state'] = 'conflict'
                receipt['resume_command'] = run_status(root, fdir, receipt).get('resume_command')
            save()
            raise


def ci_serialized(directory):
    """Only one observer updates a pushed receipt; this lock never covers building or pushing."""
    def decorate(function):
        @wraps(function)
        def finish(root, fdir, receipt, python, ci_wait):
            path = Path(fdir) / 'lane' / directory / (receipt['id'] + '.json')
            lock = Path(fdir) / 'lane/ci-locks' / (receipt['id'] + '.lock')
            lock.parent.mkdir(parents=True, exist_ok=True)
            with lock.open('a') as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                with state_lock(fdir):
                    current = read(path)
                if current.get('state') == 'done' and (current.get('integrated') or {}).get('ci') == 'green':
                    return current
                try:
                    return function(root, fdir, current, python, ci_wait)
                except BaseException as error:
                    current['error'] = str(error)
                    if directory == 'runs':
                        save_run(fdir, current)
                    else:
                        save_tooling(fdir, current)
                    raise
        return finish
    return decorate


def save_tooling(fdir, receipt):
    with state_lock(fdir):
        write(Path(fdir) / 'lane/tooling' / (receipt['id'] + '.json'), receipt)


@ci_serialized('tooling')
def finish_tooling(root, fdir, receipt, python, ci_wait):
    integ = receipt['integrated']
    receipt['owner'] = process_owner()
    save_tooling(fdir, receipt)
    result = subprocess.run([python, 'tools/ci_status.py', '--commit', integ['commit'], '--wait', str(ci_wait)],
                            cwd=root, capture_output=True, text=True)
    integ['ci'] = {0: 'green', 1: 'red', 2: 'pending'}.get(result.returncode, 'unavailable')
    ci_log = fdir / 'lane/tooling' / receipt['id'] / 'ci.log'
    with state_lock(fdir):
        atomic_write(ci_log, (result.stdout + result.stderr).encode())
    receipt['ci_log'] = str(ci_log)
    save_tooling(fdir, receipt)
    f.refuse(integ['ci'] == 'green', 'tooling CI ' + integ['ci'] + ': ' + result.stdout.strip())
    receipt.update(state='done')
    receipt.pop('error', None)
    save_tooling(fdir, receipt)
    return receipt



def signature(fdir, group):
    # Integration receipts may change without changing any gate evidence.
    value = dict(f.load_group(fdir, group))
    value.pop('integrated', None)
    return value


def gate_inputs(root, frozen, requests):
    """Pin the complete evidence consulted for these members, not other workers' gates."""
    data = f.inventory(root)
    by_id = {fn['id']: fn for fn in data['functions']}
    selected = {(r['build_id'], rva) for r in requests for rva in r['functions']}
    members = {fid for fid, fn in by_id.items() if (fn['build_id'], f.hexrva(fn['rva'])) in selected}
    records = {}

    def record(fid):
        if fid not in records:
            records[fid] = f.fr.read(root, by_id[fid]['report'])
        return records[fid]

    families, batches = f.family_manifests(root), f.family_batches(root)
    paths, relevant_families = set(), set()
    for request in requests:
        if request['kind'] == 'family':
            paths.add(request['path'])
            batch = batches[request['path']]
            members.update(batch['population'])
            relevant_families.add(batch['family_path'])
    # Individual reviews also consult family holds and the samples of bound batches.
    for path, family in families.items():
        if any(record(fid).get('origin') == family['origin']
               and f.fr.binding(by_id[fid], record(fid)) == family['binding'] for fid in members):
            relevant_families.add(path)
    sample_members = set()
    for path, batch in batches.items():
        if path in paths or any(fid in batch['population']
                                and f.fr.member_digest(by_id[fid], record(fid)) == batch['members'][fid]
                                for fid in members):
            paths.add(path)
            relevant_families.add(batch['family_path'])
            sample_members.update(batch['sample'] or [])
    members.update(sample_members)
    for path in relevant_families:
        family = families[path]
        paths.add(path)
        members.update(family['first_members'])
        if family.get('review'):
            paths.add(f.REVIEWS + '/' + family['review']['review_task_id'] + '.family.json')
        for field in ('template_source', 'parameter_source'):
            paths.add(family[field]['path'])
    referenced = {(by_id[fid]['build_id'], f.hexrva(by_id[fid]['rva'])) for fid in members}
    all_groups = f.groups(frozen)
    names = {r['group'] for r in requests if r.get('group')}
    names.update(name for name, group in all_groups.items()
                 if group.get('family_review_path') in relevant_families
                 or any((group['build_id'], rva) in referenced for rva in group['functions']))
    names.update(all_groups[name]['pair'] for name in list(names) if all_groups[name].get('pair'))
    bindings = {name: signature(frozen, name) for name in names}
    for group in bindings.values():
        paths.add(str(f.review_path(root, group).resolve()))
        if group.get('family_review_path') in relevant_families:
            paths.add(f.REVIEWS + '/' + group['task_id'] + '.family.json')
    for fid in members:
        paths.add(by_id[fid]['report'])
        paths.add(str(Path(by_id[fid]['report']).with_suffix('.review.json')))
    pins = {}
    for rel in paths:
        path = root / rel
        pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return bindings, pins


def prepare(item, frozen):
    root = Path(item['root'])
    data = f.inventory(root)
    requests, bindings = [], {}
    if item['kind'] == 'family':
        path = item['selection'][0]
        batch = f.fr.read(root, path)
        family = f.fr.read(root, batch['family_path'])
        # The unchanged acceptance function repeats every family and sampling check on the final tree.
        f.fr.validate_family(family)
        f.fr.validate_batch(batch, family)
        f.fr.private_approval(root, family, f.session_profile(frozen))
        f.fr.ordering(root, path, batch)
        by_id = {fn['id']: fn for fn in data['functions']}
        required = set(batch['sample'])
        for fid in batch['population']:
            fn = by_id[fid]
            record = f.fr.read(root, fn['report'])
            if fn['status'] == 'matched' or not f.fr.in_ranges(record.get('family_parameters'), family['parameter_ranges']):
                required.add(fid)
        functions = [f.hexrva(by_id[fid]['rva']) for fid in batch['population'] if fid not in required]
        requests.append(dict(kind='family', path=path, functions=functions,
                             build_id=family['binding']['build_id'], profile=f.session_profile(frozen)))
    elif item['kind'] == 'label':
        ids = f.af.resolve_selection(root, data, item['selection'])
        selected = [fn for fn in data['functions'] if fn['id'] in ids]
        f.refuse(len({fn['build_id'] for fn in selected}) == 1, 'label request must name one build')
        requests.append(dict(kind='label', functions=[f.hexrva(fn['rva']) for fn in selected],
                             build_id=selected[0]['build_id']))
    else:
        for name in item['selection']:
            group = f.load_group(frozen, name)
            f.refuse(group['kind'] == 'review', 'integrate requires an individual review group')
            status, blocks = f.read_review(root, group, data['functions'])
            f.refuse(status == 'ok', f'{name}: saved review {status}')
            esc = [r for r, b in blocks.items() if b.get('verdict') == 'escalate'
                   and b.get('escalation_category') in f.BLOCKING_ESCALATIONS]
            f.refuse(item['approved_only'] or not esc, f'{name}: blocking escalation; group held')
            ok, why = f.sampling_gate(root, frozen, group, data)
            f.refuse(ok, f'{name}: sampling gate: {why}')
            approved = sorted(r for r, b in blocks.items() if b.get('verdict') == 'approve'
                              and (not group.get('subset_of') or r in group['functions']))
            f.refuse(approved, f'{name}: no approvals')
            if item['kind'] == 'groups':
                f.refuse(set(approved) == set(group['functions']), f'{name}: every member needs approval')
            f.family_group_hold(root, frozen, [fn['id'] for fn in data['functions']
                                              if fn['build_id'] == group['build_id'] and f.hexrva(fn['rva']) in approved])
            bindings[name] = signature(frozen, name)
            if group.get('pair'):
                bindings[group['pair']] = signature(frozen, group['pair'])
            requests.append(dict(kind='review', group=name, review=str(f.review_path(root, group).resolve()),
                                 functions=approved, build_id=group['build_id'],
                                 profile=group.get('profile', f.profiles.DEFAULT), harvests=group.get('harvests')))
    return requests, bindings


def accept(tree, requests, python):
    request_file, result_file = tree / '.local/lane-requests.json', tree / '.local/lane-result.json'
    write(request_file, requests)
    f.run([python, str(f.TOOLS / 'lane_accept.py'), '--root', str(tree), '--requests', str(request_file),
           '--result', str(result_file)], tree, 'lane acceptance',
          env=dict(os.environ, SKYRIM_FLOW_DIR=str(tree / '.local/flow')))
    return read(result_file)


def save_run(fdir, receipt):
    with state_lock(fdir):
        write(fdir / 'lane/runs' / (receipt['id'] + '.json'), receipt)
        for item in receipt['items']:
            write(fdir / 'lane/queue' / (item['id'] + '.json'), item)
        import flow_tooling
        flow_tooling.save_items(fdir, receipt, receipt.get('state') == 'done')
        integ = receipt.get('integrated')
        if integ:
            group_members = {}
            for request in receipt.get('accepted', []):
                if request.get('group'):
                    group_members.setdefault(request['group'], set()).update(request['functions'])
            for name, members in group_members.items():
                group = f.load_group(fdir, name)
                group['integrated'] = dict(integ, accepted=len(members), lane=receipt['id'])
                f.save_group(fdir, group)


def _source_files(root, request):
    by_rva = {f.hexrva(fn['rva']): fn for fn in f.inventory(root)['functions']
              if fn['build_id'] == request['build_id']}
    paths = set()
    for rva in request['functions']:
        fn = by_rva[rva]
        paths.add(fn['report'])
        if fn.get('status') == 'matched':
            review = Path(fn['report']).with_suffix('.review.json').as_posix()
            if (root / review).is_file():
                paths.add(review)
        record = f.fr.read(root, fn['report'])
        paths.update(record['source']['translation_unit'])
        if record.get('symbol_map', {}).get('path'):
            name = record['symbol_map']['path']
            paths.add(name)
            if (root / f.history_name(name)).exists():
                paths.add(f.history_name(name))
    return by_rva, paths


def copy_private_review(source, tree, review, name=None):
    """Preserve review bytes and containment without inheriting immutable input modes."""
    review = f.review_path(source, dict(saved_review=str(review)))
    relative = review.resolve().relative_to((Path(source) / f.REVIEWS).resolve())
    destination = Path(tree) / f.REVIEWS / (name if name is not None else relative)
    destination = f.review_path(tree, dict(saved_review=str(destination)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        f.refuse(destination.read_bytes() == review.read_bytes(),
                 'conflicting saved review: ' + str(relative))
    else:
        shutil.copyfile(review, destination)
    return destination


def stale_sibling_members(tree, baseline, requests):
    """Attribute stale existing units to carried members; the whole-tree guard is unchanged.

    Inspect each distinct matched unit/digest once, not once per incoming member. Both old and
    current include closures matter when a carried header changes another unit's dependencies.
    Family selections stay atomic because their committed population/draw cannot be pruned.
    """
    changed = set(f.git(tree, 'diff', '--name-only', 'HEAD', '--', 'reconstruction').splitlines())
    changed.update(f.git(tree, 'ls-files', '--others', '--exclude-standard', '--', 'reconstruction').splitlines())
    if not changed:
        return requests, []
    current = f.inventory(tree)
    by_id = {fn['id']: fn for fn in current['functions']}
    by_address = {(fn['build_id'], f.hexrva(fn['rva'])): fn for fn in current['functions']}
    records, checked, affected = {}, set(), {}
    def source(fn):
        path = fn.get('report')
        if path not in records:
            records[path] = (f.fr.read(tree, path).get('source') or {}) if path else {}
        return records[path]
    with source_digest_cache():
        for original in baseline['functions']:
            if original['status'] != 'matched':
                continue
            fn = by_id[original['id']]
            src = source(fn)
            unit = src.get('translation_unit')
            if not isinstance(unit, list) or not all(isinstance(p, str) for p in unit):
                continue  # malformed records remain the ordinary validator's responsibility
            key = (src.get('compiled'), src.get('digest'), tuple(unit))
            if key in checked:
                continue
            checked.add(key)
            if f.af.acceptance_staleness(fn, tree) != check_gate.STALE_UNIT:
                continue
            dependencies = set(unit)
            try:
                dependencies.update(check_gate.include_closure(tree, src['compiled']))
            except (ValueError, OSError):
                pass  # retain the recorded dependencies; the final guard still checks the closure
            for name in dependencies & changed:
                affected.setdefault(name, set()).add(src['compiled'])
    if not affected:
        return requests, []
    accepted, dropped = [], []
    for request in requests:
        if not request['functions']:
            accepted.append(request)
            continue
        good, bad = [], []
        for rva in request['functions']:
            src = source(by_address[request['build_id'], rva])
            touched = set(src.get('translation_unit') or ()) & affected.keys()
            if touched:
                bad.append(dict(request=dict(request, functions=[rva]), reason='stale-sibling: needs re-confirm',
                                units=[src['compiled']], changed_paths=sorted(touched),
                                stale_sibling_units=sorted({u for name in touched for u in affected[name]})))
            else:
                good.append(rva)
        if bad and request['kind'] == 'family':
            dropped.append(dict(request=request, reason='stale-sibling: needs re-confirm',
                                units=sorted({u for d in bad for u in d['units']}),
                                changed_paths=sorted({p for d in bad for p in d['changed_paths']}),
                                stale_sibling_units=sorted({u for d in bad for u in d['stale_sibling_units']})))
        else:
            dropped.extend(bad)
            if good:
                accepted.append(dict(request, functions=good))
    return accepted, dropped


def merge_metadata(tree, source, revision):
    # integration_base validated the metadata-only history before this transport step.
    f.git(tree, 'fetch', '--quiet', str(source), revision)
    f.git(tree, 'merge', '--quiet', '--no-edit', revision)


def build(root, fdir, receipt, python, branch, soft_free_gb=None, allow_low_disk=False, hard_free_gb=None):
    try:
        resource_admission.admit(fdir, 'lane build', hard_gb=hard_free_gb,
                                 soft_gb=soft_free_gb, allow_low_disk=allow_low_disk)
    except ValueError as error:
        raise f.FlowError(str(error)) from None
    started = time.monotonic()
    receipt.setdefault('attempts', [])
    attempt = receipt.get('next_tree', 0)
    tree = fdir / 'lane/trees' / receipt['id'] / str(attempt)
    while tree.exists():
        attempt += 1
        tree = tree.with_name(str(attempt))
    receipt['next_tree'] = attempt + 1
    receipt.setdefault('candidates', []).append(str(tree))
    save_run(fdir, receipt)
    tree.parent.mkdir(parents=True, exist_ok=True)
    f.git(root, 'clone', '--quiet', '--shared', '--no-checkout', str(root), str(tree))
    # Local clone's origin points at the source checkout; use the public remote for base/push identity.
    f.git(tree, 'remote', 'set-url', 'origin', f.git(root, 'remote', 'get-url', 'origin'))
    f.git(tree, 'fetch', '--quiet', 'origin', branch)
    base = f.git(tree, 'rev-parse', f'origin/{branch}')
    f.git(tree, 'checkout', '--quiet', '--detach', base)
    for key in ('user.name', 'user.email'):
        value = f.git(root, 'config', key, check=False)
        if value:
            f.git(tree, 'config', key, value)
    import flow_tooling
    active_tools, tool_dropped = flow_tooling.merge(tree, receipt.get('tooling', []))
    receipt['tooling_accepted'], receipt['tooling_dropped'] = active_tools, tool_dropped
    baseline = f.inventory(tree) if receipt['items'] else dict(functions=[])
    carry_base = f.git(tree, 'rev-parse', 'HEAD')
    frozen = tree / '.local/flow'
    snapshot(fdir, frozen)
    requests, bindings, origins, carried, pins = [], {}, [], set(), {}
    input_pins, review_copies = {}, {}
    dropped = []
    parts = [dict(item, selection=[name]) if item['kind'] == 'groups' else item
             for item in receipt['items'] for name in (item['selection'] if item['kind'] == 'groups' else [None])]
    for item in parts:
        source = Path(item['root'])
        before_item = f.git(tree, 'rev-parse', 'HEAD')
        try:
            selected, bound = prepare(item, frozen)
            dependencies, evidence = gate_inputs(source, frozen, selected)
            bound.update(dependencies)
            input_pins.update(evidence)
            for review in sorted((source / f.REVIEWS).rglob('*')):
                if not review.is_file():
                    continue
                f.review_path(source, dict(saved_review=str(review)))
                dest = copy_private_review(source, tree, review)
                review_copies[str(review.resolve())] = dest.relative_to(tree).as_posix()

            f.git(source, 'fetch', '--quiet', 'origin', branch)
            metadata_origin = f.git(source, 'merge-base', 'HEAD', f'origin/{branch}') if item['with_metadata'] else None
            pinned_tooling = any(Path(t['root']).resolve() == source.resolve()
                                 and t['revision'] == f.git(source, 'rev-parse', 'HEAD') for t in active_tools)
            # This exact committed tip is already present through an explicit tooling input.
            # Other unpublished commits still go through the unchanged metadata-only policy.
            metadata_base = (f'origin/{branch}' if pinned_tooling else
                             f.integration_base(source, branch, item['with_metadata'], remote=metadata_origin))
            if item['with_metadata'] and metadata_base != f'origin/{branch}':
                merge_metadata(tree, source, metadata_base)
            for request in selected:
                by_rva, paths = _source_files(source, request)
                f._integration_origin_unchanged(source, f.git(source, 'rev-parse', 'HEAD'), base,
                                               sorted(paths), request['build_id'], request['functions'])
                origins.append(dict(root=str(source), base=base, paths=sorted(paths),
                                    build_id=request['build_id'], functions=request['functions'],
                                    entries={r: by_rva[r] for r in request['functions']}))
                # Never silently let one checkout overwrite a conflicting closure from another.
                for rel in paths:
                    digest = hashlib.sha256((source / rel).read_bytes()).hexdigest()
                    f.refuse(rel not in pins or pins[rel] == digest, 'incompatible queued inputs: ' + rel)
                    pins[rel] = digest
                    input_pins[str(source / rel)] = digest
                carried.update(f.carry_into_tree(source, tree, request['functions'], by_rva, request.get('harvests')))
                request['item'] = item['id']
                if request.get('review'):
                    src = Path(request['review'])
                    dest = copy_private_review(source, tree, src, item['id'] + '-' + src.name)
                    input_pins[str(src)] = hashlib.sha256(src.read_bytes()).hexdigest()
                    request['review'] = str(dest)
                # The validated recursive copy above already preserves family approval filenames.
                requests.append(request)
            bindings.update(bound)
            for group in bound.values():
                path = f.review_path(source, group).resolve()
                input_pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

        except (f.FlowError, f.af.Refused, ValueError, KeyError, TypeError, OSError) as error:
            if (tree / '.git/MERGE_HEAD').exists():
                f.git(tree, 'merge', '--abort', check=False)
            if f.git(tree, 'rev-parse', 'HEAD') != before_item:
                f.git(tree, 'reset', '--hard', before_item)
            dropped.append(dict(item=item['id'], selection=item['selection'], reason=str(error)))
    # Imported groups may name absolute paths in an input's private reviews. The frozen
    # groups must instead refer to their validated copies, including groups not selected
    # for acceptance: post-CI claims/status reads the entire frozen flow state.
    for group in f.groups(frozen).values():
        saved = group.get('saved_review')
        if saved and Path(saved).is_absolute():
            copied = review_copies.get(str(Path(saved).resolve()))
            if copied:
                group['saved_review'] = copied
                f.save_group(frozen, group)
    if not requests and not active_tools and not receipt.get('baseline_check'):
        receipt.update(dropped=dropped, state='done')
        for item in receipt['items']:
            item['state'] = 'dropped'
        save_run(fdir, receipt)
        return None
    carry_base = f.git(tree, 'rev-parse', 'HEAD')

    def recarry(selected):
        f.git(tree, 'reset', '--hard', carry_base)
        for rel in carried:
            if f.git(tree, 'ls-files', '--', rel) == '':
                (tree / rel).unlink(missing_ok=True)
        for request in selected:
            source = Path(next(i['root'] for i in receipt['items'] if i['id'] == request['item']))
            by_rva, _ = _source_files(source, request)
            f.carry_into_tree(source, tree, request['functions'], by_rva, request.get('harvests'))

    # Remove any partial carry of a request that failed before acceptance.
    if dropped:
        recarry(requests)
    while requests:
        remaining, stale = stale_sibling_members(tree, baseline, requests)
        if not stale:
            break
        dropped.extend(stale)
        requests = remaining
        recarry(requests)
    result = accept(tree, requests, python) if requests else dict(accepted=[], dropped=[], changed=[])
    if not result['accepted'] and not active_tools and not receipt.get('baseline_check'):
        receipt.update(dropped=dropped + result['dropped'], state='done')
        for item in receipt['items']:
            item['state'] = 'dropped'
        save_run(fdir, receipt)
        return None
    if result['dropped']:
        recarry(result['accepted'])
        failures = result['dropped']
        result = accept(tree, result['accepted'], python)
        f.refuse(not result['dropped'], 'accepted member changed during re-carry')
        result['dropped'] = failures
    f.refuse(result['accepted'] or active_tools or receipt.get('baseline_check'), 'no member passed acceptance')
    receipt.update(accepted=result['accepted'], dropped=dropped + result['dropped'], bindings=bindings,
                   origins=origins, input_pins=input_pins, tree=str(tree))
    if not result['accepted']:
        receipt['integrated'] = dict(commit=carry_base, accepted=0, files=[], checks=None, pushed=None, ci=None,
                                    wall_seconds={'build': time.monotonic()-started}, base_revision=base)
        if carry_base == base and active_tools and not receipt.get('baseline_check'):
            receipt['integrated'].update(checks=f.utc(), pushed=f.utc())
        save_run(fdir, receipt)
        return tree
    f.run([python, 'tools/build_progress_svg.py'], tree, 'build_progress_svg.py')
    paths = carried | set(result['changed']) | {'data/progress.json', 'reconstruction/INDEX.md',
                                              'docs/progress.svg', 'docs/progress-map.svg'}
    files = f.changed(tree, paths)
    f.refuse(files, 'nothing changed to commit')
    f.git(tree, 'add', '--', *files)
    commit_date = f.dt.datetime.now(f.dt.timezone.utc).replace(microsecond=0).isoformat()
    f.run([python, 'tools/build_model_trend.py', '--pending-date', commit_date], tree, 'build_model_trend.py')
    trend = ['README.md', 'docs/model-trend.svg', 'docs/progress-trend.svg']
    f.git(tree, 'add', '--', *trend)
    f.run([python, 'tools/check.py', '--staged'], tree, 'check.py --staged')
    f.run(['git', 'commit', '--quiet', '-m', f'Accept queued work in push lane {receipt["id"]}'], tree, 'git commit',
          env=dict(os.environ, GIT_COMMITTER_DATE=commit_date))
    integ = dict(commit=f.git(tree, 'rev-parse', 'HEAD'), accepted=sum(len(r['functions']) for r in result['accepted']),
                 files=sorted(set(files) | set(trend)), checks=None, pushed=None, ci=None,
                 wall_seconds={'build': time.monotonic() - started}, base_revision=base)
    receipt['integrated'] = integ
    save_run(fdir, receipt)
    return tree


def disk_preflight(fdir, min_free_gb=None):
    """Refuse expensive lane work below the configured free-space threshold (decimal GB)."""
    setting = min_free_gb if min_free_gb is not None else os.environ.get('SKYRIM_LANE_MIN_FREE_GB', '3')
    try:
        threshold = float(setting)
    except (TypeError, ValueError):
        raise f.FlowError('minimum free disk space must be a finite nonnegative number of GB') from None
    f.refuse(math.isfinite(threshold) and threshold >= 0,
             'minimum free disk space must be a finite nonnegative number of GB')
    path = Path(fdir)
    while not path.exists():
        path = path.parent
    free = shutil.disk_usage(path).free / 1_000_000_000
    f.refuse(free >= threshold,
             f'insufficient free disk space for push lane: {free:.2f} GB free; need {threshold:g} GB. '
             'Free disk space or configure --min-free-gb / SKYRIM_LANE_MIN_FREE_GB.')


def run_lane(root, fdir, branch='main', push=True, ci_wait=600, python=sys.executable, min_free_gb=None,
             soft_free_gb=None, allow_low_disk=False, resume=None, wait_lane=False):
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    python = lane_python(python)
    if resume and receipt_path(fdir, resume).parent.name == 'tooling':
        f.refuse(push, 'tooling resume requires push/CI mode; use tooling-push --resume ' + resume)
        return publish_tooling(root, fdir, branch, ci_wait, python, resume=resume,
                               soft_free_gb=soft_free_gb, allow_low_disk=allow_low_disk)
    if resume:
        with state_lock(fdir):
            previous = read(receipt_path(fdir, resume))
        if (previous.get('integrated') or {}).get('pushed'):
            return finish_run(root, fdir, previous, python, ci_wait)
    disk_preflight(fdir, min_free_gb)
    wait_for_owner(root, fdir, 'runs', resume, wait_lane)
    wait_for_owner(root, fdir, 'tooling', None, wait_lane)
    with lane_lock(fdir, wait=wait_lane, purpose='integration') as lease:
        recover_stale(fdir)
        with state_lock(fdir):
            require_complete(fdir)
            unfinished = [read(p) for p in sorted((fdir / 'lane/runs').glob('*.json')) if read(p)['state'] == 'running' and not (read(p).get('integrated') or {}).get('pushed')]
            unfinished = [r for r in unfinished if r.get('root') == str(root)]
            if resume:
                selected = read(receipt_path(fdir, resume))
                f.refuse(selected['state'] in ('running', 'failed', 'conflict', 'stale'), 'receipt cannot be resumed')
                unfinished = [selected]
            f.refuse(len(unfinished) <= 1, 'multiple unfinished lane runs')
            if unfinished:
                receipt = unfinished[0]
                f.refuse(not resume or receipt['id'] == resume, 'resume id is not the unfinished lane run')
                f.refuse(receipt['branch'] == branch, 'resume lane with the same branch')
            else:
                f.refuse(not resume, 'no unfinished lane run with that id')
                items = [read(p) for p in sorted((fdir / 'lane/queue').glob('*.json')) if read(p)['state'] == 'queued']
                import flow_tooling
                tooling = [read(p) for p in sorted((fdir / 'lane/tooling-queue').glob('*.json'))
                           if read(p)['state'] == 'queued' and read(p)['branch'] == branch]
                tooling.sort(key=lambda i: (i['queued_at'], i['id']))
                if tooling and not flow_tooling.mixed_safe(tooling):
                    items = []  # Gate-changing tooling publishes before function acceptances.
                if not items and not tooling:
                    return dict(state='empty')
                f.refuse(all(i['branch'] == branch for i in items), 'queued requests name different branches')
                receipt = dict(id=uuid.uuid4().hex[:16], root=str(root), branch=branch, items=items, tooling=tooling, state='running', integrated=None)
                for item in items:
                    item['state'], item['run'] = 'running', receipt['id']
                save_run(fdir, receipt)
            guard_cleanup(fdir, root)
            if receipt.get('tree'):
                guard_cleanup(fdir, receipt['tree'])
            receipt['owner'] = process_owner()
            receipt.update(state='running', python=python)
            save_run(fdir, receipt)
        try:
            while True:
                if not receipt.get('integrated'):
                    if build(root, fdir, receipt, python, branch, soft_free_gb, allow_low_disk, min_free_gb) is None:
                        return receipt
                tree, integ = Path(receipt['tree']), receipt['integrated']
                # Avoid checking an obsolete candidate when resuming after a failed check.
                if not integ['pushed']:
                    f.git(tree, 'fetch', '--quiet', 'origin', branch)
                    destination = f.git(tree, 'rev-parse', f'origin/{branch}')
                    if destination != integ['base_revision']:
                        for origin in receipt['origins']:
                            f._integration_origin_unchanged(tree, origin['base'], destination, origin['paths'],
                                                          origin['build_id'], origin['functions'])
                        receipt['attempts'].append(integ)
                        receipt['integrated'] = None
                        save_run(fdir, receipt)
                        continue
                if not integ['checks']:
                    started = time.monotonic()
                    logs = fdir / 'lane/logs' / receipt['id'] / str(len(receipt.get('attempts', [])))
                    receipt['checks_log_dir'] = str(logs)
                    save_run(fdir, receipt)
                    try:
                        f.pre_push_checks(tree, integ['commit'], python, candidate=True, log_dir=logs,
                                          base_revision=integ['base_revision'])
                    except f.FlowError as error:
                        if not receipt.get('tooling_accepted'):
                            raise
                        import flow_tooling
                        flow_tooling.isolate_failure(root, fdir, receipt, python, branch, error)
                        if receipt['state'] == 'done':
                            return receipt
                        tree, integ = Path(receipt['tree']), receipt['integrated']
                    integ['checks'] = f.utc()
                    integ['wall_seconds']['checks'] = time.monotonic() - started
                    save_run(fdir, receipt)
                if not push:
                    return receipt
                if not integ['pushed']:
                    require_green(tree, integ['base_revision'], python, ci_wait)
                    # Re-read the live scheduling gates just before publishing the frozen tree.
                    with state_lock(fdir):
                        for name, pinned in receipt['bindings'].items():
                            f.refuse(signature(fdir, name) == pinned, 'gate state changed during lane run: ' + name)
                    for origin in receipt['origins']:
                        current = {f.hexrva(fn['rva']): fn for fn in f.inventory(Path(origin['root']))['functions']
                                   if fn['build_id'] == origin['build_id']}
                        f.refuse(all(current.get(r) == row for r, row in origin['entries'].items()),
                                 'selected inventory changed during lane run')
                    for path, digest in receipt['input_pins'].items():
                        actual = hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else None
                        f.refuse(actual == digest,
                                 'queued input changed during lane run: ' + path)
                    f.git(tree, 'fetch', '--quiet', 'origin', branch)
                    destination = f.git(tree, 'rev-parse', f'origin/{branch}')
                    if destination != integ['base_revision']:
                        for origin in receipt['origins']:
                            f._integration_origin_unchanged(tree, origin['base'], destination, origin['paths'],
                                                          origin['build_id'], origin['functions'])
                        receipt['attempts'].append(integ)
                        receipt['integrated'] = None
                        save_run(fdir, receipt)
                        continue
                    f.refuse(f.git(tree, 'rev-parse', 'HEAD') == integ['commit']
                             and not f.git(tree, 'status', '--porcelain', '--untracked-files=no'),
                             'candidate changed after checks; refusing push')
                    try:
                        f.run(['git', 'push', 'origin', f'{integ["commit"]}:refs/heads/{branch}'], tree, 'git push')
                    except f.FlowError as error:
                        if 'non-fast-forward' not in str(error) and 'fetch first' not in str(error):
                            raise
                        # The next iteration observes the winner and rebuilds through unchanged gates.
                        continue
                    integ['pushed'] = f.utc()
                    save_run(fdir, receipt)
                lease.release()
                receipt['lane_hold_seconds'] = lease.seconds
                save_run(fdir, receipt)
                return finish_run(root, fdir, receipt, python, ci_wait)

        except BaseException as error:
            if (receipt.get('integrated') or {}).get('pushed'):
                raise
            receipt['error'] = str(error)
            save_run(fdir, receipt)
            raise


@ci_serialized('runs')
def finish_run(root, fdir, receipt, python, ci_wait):
    tree, integ = Path(receipt['tree']), receipt['integrated']
    integ.setdefault('accepted', sum(len(r.get('functions', [])) for r in receipt.get('accepted', [])))
    branch = receipt['branch']
    receipt['owner'] = process_owner()
    save_run(fdir, receipt)
    if integ['ci'] != 'green':
        started = time.monotonic()
        result = subprocess.run([python, 'tools/ci_status.py', '--commit', integ['commit'], '--wait', str(ci_wait)],
                                cwd=tree, capture_output=True, text=True)
        log = fdir / 'lane/logs' / receipt['id'] / 'ci.log'
        with state_lock(fdir):
            atomic_write(log, (result.stdout + result.stderr).encode())
        receipt['ci_log'] = str(log)
        integ['ci'] = {0: 'green', 1: 'red', 2: 'pending'}.get(result.returncode, 'unavailable')
        integ['wall_seconds']['ci'] = time.monotonic() - started
        save_run(fdir, receipt)
        f.refuse(integ['ci'] == 'green', f'CI {integ["ci"].upper()} for {integ["commit"]}: {result.stdout.strip()}')
    # The shared checkout needs the new remote ref so next-actions offers sync.
    f.git(root, 'fetch', '--quiet', 'origin', branch)
    receipt.pop('error', None)
    receipt['state'] = 'done'
    accepted_items = {r['item'] for r in receipt['accepted']}
    for item in receipt['items']:
        item['state'] = 'done' if item['id'] in accepted_items else 'dropped'
    save_run(fdir, receipt)
    f.log_event(fdir, 'integrated', lane=receipt['id'], accepted=integ['accepted'], commit=integ['commit'])
    f.log_event(fdir, 'ci', lane=receipt['id'], result=integ['ci'], commit=integ['commit'])
    if receipt.get('accepted'):
        import claims
        claims.sync_safe(tree)
    return receipt
