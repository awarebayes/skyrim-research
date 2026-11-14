"""One durable push lane. The live state lock is used only for queue/receipt mutations.

Candidates are independent local clones with private flow snapshots. No branch, stash or
worktree is removed, including failed candidates. A run drains one frozen queue snapshot.
"""
from contextlib import contextmanager
import fcntl
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
from flow_state import state_lock, atomic_write, require_complete


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    atomic_write(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def enqueue(root, fdir, kind, selection, branch='main', approved_only=False, with_metadata=False, name=None):
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    payload = dict(root=str(root), kind=kind, selection=selection, branch=branch,
                   approved_only=approved_only, with_metadata=with_metadata, name=name)
    key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    path = fdir / 'lane/queue' / (key + '.json')
    with state_lock(fdir):
        require_complete(fdir)
        for reservation in (fdir / 'cleanup/claims').glob('*.json'):
            claim = read(reservation)
            f.refuse(not claim.get('active') or not root.is_relative_to(Path(claim['tree'])),
                     'input checkout is being cleaned; retry after cleanup with a retained input')
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
        try:
            yield
        finally:
            if purpose:
                with state_lock(fdir):
                    owner = read(owner_path)
                    owner['active'] = False
                    write(owner_path, owner)
            fcntl.flock(handle, fcntl.LOCK_UN)


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
        for name in ('groups', 'imports', 'combined', 'lane/queue', 'lane/runs', 'lane/tooling'):
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
    if receipt.get('state') == 'running':
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
        if command == 'lane-run' and not (receipt.get('integrated') or {}).get('pushed'):
            value['retire_command'] = prefix + ' lane-retire ' + receipt['id'] + " --reason 'owner stopped; selection superseded'"
    return value


def retire(root, fdir, run_id, reason):
    f.refuse(run_id and Path(run_id).name == run_id and run_id not in ('.', '..'), 'invalid run id')
    with lane_lock(fdir), state_lock(fdir):
        receipt = read(Path(fdir) / 'lane/runs' / (run_id + '.json'))
        f.refuse(receipt['state'] == 'running', 'only an unfinished run can be retired')
        f.refuse(not (receipt.get('integrated') or {}).get('pushed'), 'pushed run must resume CI; cannot retire it')
        receipt.update(state='retired', retired_at=f.utc(), retirement_reason=reason)
        for item in receipt['items']:
            item['state'] = 'retired'
        save_run(fdir, receipt)
        return receipt


def publish_tooling(root, fdir, branch='main', ci_wait=600, python=sys.executable, resume=None, wait_lane=False,
                    soft_free_gb=None, allow_low_disk=False):
    """Check and publish committed tooling under the same lane lock as acceptance work."""
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    with lane_lock(fdir, wait=wait_lane, purpose='tooling'):
        with state_lock(fdir):
            pending = [read(p) for p in (fdir / 'lane/tooling').glob('*.json') if read(p)['state'] == 'running']
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
            receipt['owner'] = process_owner()
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
            result = subprocess.run([python, 'tools/ci_status.py', '--commit', integ['commit'], '--wait', str(ci_wait)],
                                    cwd=root, capture_output=True, text=True)
            integ['ci'] = {0: 'green', 1: 'red', 2: 'pending'}.get(result.returncode, 'unavailable')
            ci_log = fdir / 'lane/tooling' / receipt['id'] / 'ci.log'
            with state_lock(fdir):
                atomic_write(ci_log, (result.stdout + result.stderr).encode())
            receipt['ci_log'] = str(ci_log)
            save()
            f.refuse(integ['ci'] == 'green', 'tooling CI ' + integ['ci'] + ': ' + result.stdout.strip())
            receipt.update(state='done')
            receipt.pop('error', None)
            save()
            return receipt
        except BaseException as error:
            receipt['error'] = str(error)
            save()
            raise


def signature(fdir, group):
    # Integration receipts may change without changing any gate evidence.
    value = dict(f.load_group(fdir, group))
    value.pop('integrated', None)
    return value


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
        record = f.fr.read(root, fn['report'])
        paths.update(record['source']['translation_unit'])
        if record.get('symbol_map', {}).get('path'):
            name = record['symbol_map']['path']
            paths.add(name)
            if (root / f.history_name(name)).exists():
                paths.add(f.history_name(name))
    return by_rva, paths


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
            for review in sorted((source / f.REVIEWS).glob('*')):
                if not review.is_file():
                    continue
                f.review_path(source, dict(saved_review=str(review)))
                dest = tree / f.REVIEWS / review.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                f.refuse(not dest.exists() or dest.read_bytes() == review.read_bytes(),
                         'conflicting saved review: ' + review.name)
                shutil.copyfile(review, dest)
                input_pins[str(review.resolve())] = hashlib.sha256(review.read_bytes()).hexdigest()
                review_copies[str(review.resolve())] = dest.relative_to(tree).as_posix()
            for request in selected:
                if request['kind'] == 'family':
                    batch = f.fr.read(source, request['path'])
                    for rel in (request['path'], batch['family_path']):
                        input_pins[str(source / rel)] = hashlib.sha256((source / rel).read_bytes()).hexdigest()
                    # Family sampling checks may consult any individually reviewed population member.
                    bound.update({n: signature(frozen, n) for n in f.groups(frozen)})

            f.git(source, 'fetch', '--quiet', 'origin', branch)
            metadata_origin = f.git(source, 'merge-base', 'HEAD', f'origin/{branch}') if item['with_metadata'] else None
            metadata_base = f.integration_base(source, branch, item['with_metadata'], remote=metadata_origin)
            if item['with_metadata'] and metadata_base != f'origin/{branch}':
                f.git(tree, 'merge', '--quiet', '--no-edit', metadata_base)
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
                    dest = tree / '.local/reviews' / (item['id'] + '-' + src.name)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dest)
                    input_pins[str(src)] = hashlib.sha256(src.read_bytes()).hexdigest()
                    request['review'] = str(dest)
                # Family approval filenames must retain the names bound by the manifest.
                if request['kind'] == 'family':
                    shutil.copytree(source / f.REVIEWS, tree / f.REVIEWS, dirs_exist_ok=True)
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
    if not requests:
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
    result = accept(tree, requests, python)
    if not result['accepted']:
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
    f.refuse(result['accepted'], 'no member passed acceptance')
    receipt.update(accepted=result['accepted'], dropped=dropped + result['dropped'], bindings=bindings,
                   origins=origins, input_pins=input_pins, tree=str(tree))
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


def settle_legacy_ci(root, fdir, python, ci_wait):
    """Finish pre-lane pushed checkpoints before any new push; never rebuild their acceptances."""
    with state_lock(fdir):
        pending = {g['integrated']['commit'] for g in f.groups(fdir).values()
                   if (g.get('integrated') or {}).get('pushed') and g['integrated'].get('ci') != 'green'}
        pending.update(r['integrated']['commit'] for p in (fdir / 'lane/tooling').glob('*.json')
                       if ((r := read(p)).get('integrated') or {}).get('pushed') and r['integrated'].get('ci') != 'green')
    for commit in sorted(pending):
        result = subprocess.run([python, 'tools/ci_status.py', '--commit', commit, '--wait', str(ci_wait)],
                                cwd=root, capture_output=True, text=True)
        ci = {0: 'green', 1: 'red', 2: 'pending'}.get(result.returncode, 'unavailable')
        with state_lock(fdir):
            for group in f.groups(fdir).values():
                if (group.get('integrated') or {}).get('commit') == commit:
                    group['integrated']['ci'] = ci
                    f.save_group(fdir, group)
            for path in (fdir / 'combined').glob('*.json'):
                transaction = read(path)
                if (transaction.get('integrated') or {}).get('commit') == commit:
                    transaction['integrated']['ci'] = ci
                    write(path, transaction)
            for path in (fdir / 'lane/tooling').glob('*.json'):
                publication = read(path)
                if (publication.get('integrated') or {}).get('commit') == commit:
                    publication['integrated']['ci'] = ci
                    if ci == 'green':
                        publication['state'] = 'done'
                        publication.pop('error', None)
                    write(path, publication)
        f.refuse(ci == 'green', f'CI {ci.upper()} for previous integration {commit}: {result.stdout.strip()}')


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
             soft_free_gb=None, allow_low_disk=False, resume=None):
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    disk_preflight(fdir, min_free_gb)
    with lane_lock(fdir, purpose='integration'):
        settle_legacy_ci(root, fdir, python, ci_wait)
        with state_lock(fdir):
            require_complete(fdir)
            unfinished = [read(p) for p in sorted((fdir / 'lane/runs').glob('*.json')) if read(p)['state'] == 'running']
            f.refuse(len(unfinished) <= 1, 'multiple unfinished lane runs')
            if unfinished:
                receipt = unfinished[0]
                f.refuse(not resume or receipt['id'] == resume, 'resume id is not the unfinished lane run')
                f.refuse(receipt['branch'] == branch, 'resume lane with the same branch')
            else:
                f.refuse(not resume, 'no unfinished lane run with that id')
                items = [read(p) for p in sorted((fdir / 'lane/queue').glob('*.json')) if read(p)['state'] == 'queued']
                if not items:
                    return dict(state='empty')
                f.refuse(all(i['branch'] == branch for i in items), 'queued requests name different branches')
                receipt = dict(id=uuid.uuid4().hex[:16], root=str(root), branch=branch, items=items, state='running', integrated=None)
                for item in items:
                    item['state'], item['run'] = 'running', receipt['id']
                save_run(fdir, receipt)
            receipt['owner'] = process_owner()
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
                    f.pre_push_checks(tree, integ['commit'], python, candidate=True)
                    integ['checks'] = f.utc()
                    integ['wall_seconds']['checks'] = time.monotonic() - started
                    save_run(fdir, receipt)
                if not push:
                    return receipt
                if not integ['pushed']:
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
                if integ['ci'] != 'green':
                    started = time.monotonic()
                    result = subprocess.run([python, 'tools/ci_status.py', '--commit', integ['commit'], '--wait', str(ci_wait)],
                                            cwd=tree, capture_output=True, text=True)
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
                import claims
                claims.sync_safe(tree)
                return receipt
        except BaseException as error:
            receipt['error'] = str(error)
            save_run(fdir, receipt)
            raise
