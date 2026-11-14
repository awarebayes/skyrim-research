"""Pinned tooling inputs for the shared acceptance lane; no input checkout is changed."""
import hashlib
import json
import math
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
            if previous['state'] in ('queued', 'running', 'done', 'dropped'):
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
            if old['state'] in ('queued', 'running', 'done', 'dropped'):
                return old
        item = dict(id=key, root=str(root), revision=revision, base=base, branch=branch,
                    paths=paths, state='queued', queued_at=f.dt.datetime.now(f.dt.timezone.utc).isoformat())
        lane.write(path, item)
        f.log_event(Path(fdir), 'tooling-queued', request=key, revision=revision)
        return item


def save_items(fdir, receipt, finished=False):
    import flow_lane as lane
    dropped = {d['item']: d['reason'] for d in receipt.get('tooling_dropped', [])}
    accepted = {i['id'] for i in receipt.get('tooling_accepted', [])}
    for item in receipt.get('tooling', []):
        previous = item['state']
        item['run'] = receipt['id']
        item['state'] = ('dropped' if item['id'] in dropped else
                         receipt['state'] if receipt.get('state') in ('retired', 'stale', 'failed', 'conflict') else
                         'done' if finished else 'running')
        if item['id'] in dropped:
            item['reason'] = dropped[item['id']]
        else:
            item.pop('reason', None)
        item['integrated'] = receipt.get('integrated') if item['id'] in accepted else None
        item['error'] = receipt.get('error')
        lane.write(Path(fdir) / 'lane/tooling-queue' / (item['id'] + '.json'), item)
        # A request receipt is an outcome/reference, never a second lane owner.
        lane.write(Path(fdir) / 'lane/tooling' / (item['id'] + '.json'),
                   dict(item, kind='tooling-request', owner=receipt.get('owner')))
        if item['state'] in ('done', 'dropped') and item['state'] != previous:
            f.log_event(Path(fdir), 'tooling-outcome', request=item['id'], lane=receipt['id'],
                        revision=item['revision'], result=item['state'], reason=item.get('reason'),
                        commit=(item.get('integrated') or {}).get('commit'))


def merge(tree, items):
    """Merge immutable tips, retaining successful inputs and explaining each conflicting input."""
    accepted, dropped = [], []
    for item in items:
        if item.get('state') == 'dropped':
            dropped.append(dict(item=item['id'], revision=item['revision'],
                                reason=item.get('reason') or 'previously bounced tooling input'))
            continue
        before = f.git(tree, 'rev-parse', 'HEAD')
        try:
            f.git(tree, 'fetch', '--quiet', item['root'], item['revision'])
            f.git(tree, 'merge', '--quiet', '--no-edit', '--no-ff', item['revision'])
            accepted.append(item)
        except f.FlowError as error:
            f.git(tree, 'merge', '--abort', check=False)
            f.git(tree, 'reset', '--hard', before)
            dropped.append(dict(item=item['id'], revision=item['revision'], reason=str(error)))
    return accepted, dropped


def publish(root, fdir, branch, ci_wait, python, soft_free_gb, allow_low_disk, wait_lane=True):
    import flow_lane as lane
    item = enqueue(root, fdir, branch)
    path = Path(fdir) / 'lane/tooling-queue' / (item['id'] + '.json')

    def outcome():
        with state_lock(fdir):
            current = lane.read(path)
            receipt = (lane.read(Path(fdir) / 'lane/runs' / (current['run'] + '.json'))
                       if current.get('run') else None)
        f.refuse(current['state'] != 'dropped',
                 'tooling input ' + current['revision'] + ' bounced: ' + current.get('reason', 'check failure'))
        f.refuse(current['state'] not in ('retired', 'stale', 'failed', 'conflict'),
                 'tooling request ' + current['state'] + ': ' + (current.get('error') or 'resume its lane run'))
        return current, receipt

    while True:
        current, receipt = outcome()
        if receipt and (receipt.get('integrated') or {}).get('pushed'):
            if receipt['state'] != 'done':
                receipt = lane.finish_run(root, fdir, receipt, python, ci_wait)
            return dict(receipt, request=lane.read(path))
        if receipt and receipt.get('error'):
            raise f.FlowError(receipt['error'])
        if receipt and lane.owner_alive(receipt.get('owner')) and lane.running(fdir):
            f.refuse(wait_lane, 'push lane already running; queued request ' + current['id'])
            time.sleep(0.25)
            continue
        try:
            lane.run_lane(root, fdir, branch, True, ci_wait, python,
                          resume=receipt['id'] if receipt else None, wait_lane=wait_lane,
                          soft_free_gb=soft_free_gb, allow_low_disk=allow_low_disk)
        except f.FlowError:
            # Another runner may have completed our request while this runner waited.
            current, receipt = outcome()
            if current['state'] != 'done':
                raise


def isolate_failure(root, fdir, receipt, python, branch, error, soft_free_gb=None,
                    allow_low_disk=False, hard_free_gb=None):
    """Bisect failed tooling batches, at most ceil(log2(n)) split levels.

    Prove the baseline first, then test halves on top of the accumulated good inputs in
    queue order. Each passing trial is the complete prospective tree, so the final survivor
    already has full checks; we never infer a combined pass from separately checked halves.
    One bad input costs O(log n) probes; multiple failures may need probes at each split.
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
    accepted, failures, trials = [], list(original.get('tooling_dropped', [])), []
    best = None
    limit = math.ceil(math.log2(len(inputs))) if inputs else 0

    def probe(items, depth):
        nonlocal best
        trial = json.loads(json.dumps(original))
        trial.update(tooling=accepted + items, integrated=None, baseline_check=True,
                     state='running', error=None)
        row = dict(round=depth, revisions=[i['revision'] for i in items])
        trials.append(row)
        try:
            lane.build(root, private, trial, python, branch, soft_free_gb, allow_low_disk, hard_free_gb)
            f.refuse(not trial.get('tooling_dropped'), 'tooling inputs failed to apply during bisection: '
                     + str(trial.get('tooling_dropped')))
            integ = trial['integrated']
            logs = private / 'check-logs' / str(len(trials))
            trial['checks_log_dir'] = str(logs)
            row.update(tree=trial['tree'], logs=str(logs), commit=integ['commit'])
            f.pre_push_checks(Path(trial['tree']), integ['commit'], python, candidate=True, log_dir=logs,
                              base_revision=integ['base_revision'])
        except f.FlowError as failure:
            row.update(result='failed', reason=str(failure))
            return str(failure)
        row['result'] = 'passed'
        integ['checks'] = f.utc()
        best = trial
        accepted.extend(items)
        return None

    baseline_error = probe([], 0)
    if baseline_error:
        receipt['bisection'] = dict(max_rounds=limit, trials=trials)
        lane.save_run(fdir, receipt)
        raise f.FlowError('whole-tree baseline check failed: ' + baseline_error) from error

    def split(items, depth, known_failure=None):
        failure = known_failure or probe(items, depth)
        if not failure:
            return
        if len(items) == 1:
            item = items[0]
            failures.append(dict(item=item['id'], revision=item['revision'],
                                 reason='combined check: ' + failure))
            return
        f.refuse(depth < limit, 'tooling bisection round limit exceeded')
        middle = len(items) // 2
        split(items[:middle], depth + 1)
        split(items[middle:], depth + 1)

    if inputs:
        split(inputs, 0, str(error))
    receipt.update(best)
    receipt.update(tooling=original['tooling'], tooling_accepted=accepted, tooling_dropped=failures,
                   bisection=dict(max_rounds=limit, trials=trials))
    receipt.pop('baseline_check', None)
    receipt.pop('error', None)
    if not accepted and not receipt.get('accepted'):
        receipt['state'] = 'done'
        receipt['integrated'] = None
    lane.save_run(fdir, receipt)
    f.log_event(Path(fdir), 'lane-bisected', lane=receipt['id'], rounds=max(t['round'] for t in trials),
                probes=len(trials), bounced=[d.get('revision') for d in failures])
    return receipt
