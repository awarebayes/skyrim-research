"""Pinned tooling inputs for the shared acceptance lane; no input checkout is changed."""
import hashlib
import json
from pathlib import Path
import time

import flow as f
from flow_state import state_lock


def enqueue(root, fdir, branch):
    import flow_lane as lane
    f.refuse(not f.git(root, 'status', '--porcelain', '--untracked-files=all'),
             'tooling-push requires a clean, committed checkout')
    revision = f.git(root, 'rev-parse', 'HEAD')
    key = hashlib.sha256((str(root) + revision + branch).encode()).hexdigest()[:24]
    path = Path(fdir) / 'lane/tooling-queue' / (key + '.json')
    with state_lock(fdir):
        if path.is_file():
            previous = lane.read(path)
            if previous['state'] in ('queued', 'running', 'done'):
                return previous
    f.git(root, 'fetch', '--quiet', 'origin', branch)
    base = f.git(root, 'merge-base', revision, 'origin/' + branch)
    paths = f.git(root, 'diff', '--name-only', base, revision).splitlines()
    f.refuse(paths, 'no tooling commit to push')
    with state_lock(fdir):
        for claim_file in (Path(fdir) / 'cleanup/claims').glob('*.json'):
            claim = lane.read(claim_file)
            f.refuse(not claim.get('active') or not Path(root).is_relative_to(Path(claim['tree'])),
                     'input checkout is being cleaned; retry with a retained input')
        if path.is_file():
            old = lane.read(path)
            if old['state'] in ('queued', 'running', 'done'):
                return old
        item = dict(id=key, root=str(root), revision=revision, base=base, branch=branch,
                    paths=paths, state='queued', queued_at=f.dt.datetime.now(f.dt.timezone.utc).isoformat())
        lane.write(path, item)
        return item


def mixed_safe(items):
    # A function acceptance must use the same admitted gate machinery it was queued with.
    protected = ('tools/accept_function', 'tools/check', 'tools/compare', 'tools/family_review',
                 'tools/flow', 'tools/lint', 'tools/source_digest', 'tools/verifier/',
                 'docs/verification.md', 'docs/authorizations.md')
    return not any(path.startswith(protected) for item in items for path in item['paths'])


def save_items(fdir, receipt, finished=False):
    import flow_lane as lane
    dropped = {d['item']: d['reason'] for d in receipt.get('tooling_dropped', [])}
    for item in receipt.get('tooling', []):
        item['run'] = receipt['id']
        item['state'] = (receipt['state'] if receipt.get('state') in ('retired', 'stale', 'failed', 'conflict') else
                         'dropped' if item['id'] in dropped else 'done' if finished else 'running')
        if item['id'] in dropped:
            item['reason'] = dropped[item['id']]
        lane.write(Path(fdir) / 'lane/tooling-queue' / (item['id'] + '.json'), item)


def merge(tree, items):
    """Merge immutable tips, retaining successful inputs and explaining each conflicting input."""
    accepted, dropped = [], []
    for item in items:
        before = f.git(tree, 'rev-parse', 'HEAD')
        try:
            f.git(tree, 'fetch', '--quiet', item['root'], item['revision'])
            f.git(tree, 'merge', '--quiet', '--no-edit', '--no-ff', item['revision'])
            accepted.append(item)
        except f.FlowError as error:
            f.git(tree, 'merge', '--abort', check=False)
            f.git(tree, 'reset', '--hard', before)
            dropped.append(dict(item=item['id'], reason=str(error)))
    return accepted, dropped


def publish(root, fdir, branch, ci_wait, python, soft_free_gb, allow_low_disk):
    import flow_lane as lane
    item = enqueue(root, fdir, branch)
    path = Path(fdir) / 'lane/tooling-queue' / (item['id'] + '.json')
    while True:
        with state_lock(fdir):
            current = lane.read(path)
            receipt = (lane.read(Path(fdir) / 'lane/runs' / (current['run'] + '.json'))
                       if current.get('run') else None)
        f.refuse(current['state'] != 'dropped', 'tooling input dropped: ' + current.get('reason', 'check failure'))
        if receipt and (receipt.get('integrated') or {}).get('pushed'):
            if receipt['state'] == 'done':
                return receipt
            return lane.finish_run(root, fdir, receipt, python, ci_wait)
        if receipt:
            if not lane.owner_alive(receipt.get('owner')):
                lane.run_lane(root, fdir, branch, True, ci_wait, python, resume=receipt['id'], wait_lane=True,
                              soft_free_gb=soft_free_gb, allow_low_disk=allow_low_disk)
                continue
            time.sleep(0.25)
            continue
        lane.run_lane(root, fdir, branch, True, ci_wait, python,
                      soft_free_gb=soft_free_gb, allow_low_disk=allow_low_disk, wait_lane=True)


def isolate_failure(root, fdir, receipt, python, branch, error):
    """Only on a failed combined check: prove the function/base tree, then retain good prefixes.

    Diagnostic candidates and receipts are private copies. A failed baseline is a whole-tree
    failure, not evidence against a tooling input. Successful batches never take this path.
    """
    import flow_lane as lane
    original = json.loads(json.dumps(receipt))
    inputs = original.get('tooling_accepted', [])
    private = Path(fdir) / 'lane/isolation' / receipt['id']
    suffix = 0
    while private.exists():
        suffix += 1
        private = private.with_name(receipt['id'] + '-' + str(suffix))
    lane.snapshot(fdir, private)
    accepted, failures = [], list(original.get('tooling_dropped', []))
    best = None
    for number, item in enumerate([None, *inputs]):
        trial = json.loads(json.dumps(original))
        trial.update(tooling=accepted + ([item] if item else []), integrated=None,
                     baseline_check=True, state='running')
        lane.build(root, private, trial, python, branch)
        integ = trial['integrated']
        try:
            logs = private / 'check-logs' / str(number)
            trial['checks_log_dir'] = str(logs)
            f.pre_push_checks(Path(trial['tree']), integ['commit'], python, candidate=True, log_dir=logs)
        except f.FlowError as failure:
            if item is None:
                raise f.FlowError('whole-tree baseline check failed: ' + str(failure)) from error
            failures.append(dict(item=item['id'], reason='combined check: ' + str(failure)))
            continue
        if item:
            accepted.append(item)
        integ['checks'] = f.utc()
        best = trial
    f.refuse(best is not None, 'no checked baseline after tooling failure')
    receipt.update(best)
    receipt.update(tooling=original['tooling'], tooling_accepted=accepted, tooling_dropped=failures)
    if not accepted and not receipt.get('accepted'):
        # Every input failed; nothing is repushed and the known baseline is retained as evidence.
        receipt['state'] = 'done'
        receipt['integrated'] = None
    lane.save_run(fdir, receipt)
    return receipt
