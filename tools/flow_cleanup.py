"""Opt-in lifecycle cleanup; retain immutable inputs, receipts, evidence and Git refs."""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

import flow as f
import flow_lane as lane

FINISHED = {'done', 'retired', 'stale', 'failed'}
TIERS = ('first', 'fallback', 'strong')


def finished(receipt):
    integrated = receipt.get('integrated') or {}
    return (receipt.get('state') in FINISHED
            and integrated.get('ci') != 'pending'
            and not (integrated.get('pushed') and integrated.get('ci') not in ('green', 'red')))


def claim_harvest(root, queue, unit, tier):
    directory = f.drafts.task_dir(root, unit)
    done_path = f.wq.tier_dir(queue, 'done', tier) / (unit['key'] + '.json')
    done = f.drafts.read(done_path, {})
    harvest = (done.get('harvest') or f.drafts.read(directory / ('harvest-' + tier + '.json'))
               or f.drafts.read(directory / 'harvest.json', {}))
    f.refuse(not any((f.wq.tier_dir(q.parent, 'claims', t) / (unit['key'] + '.lock')).exists()
                     for q in (root / '.local/queue').glob('*/queue.tsv') for t in TIERS),
             'draft claim is open or drafting')
    f.refuse(done_path.is_file() and harvest.get('tier') == tier and bool(harvest.get('commit')),
             'no completed unit harvest for this tier')
    commit = harvest['commit']
    f.refuse(len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'invalid harvest commit')
    f.refuse(f.git(root, 'cat-file', '-t', commit, check=False) == 'commit', 'harvest commit missing from object store')
    return harvest


def candidates(root, fdir, prune_claims=False):
    for receipt in (fdir / 'lane/runs').glob('*.json'):
        r = lane.read(receipt)
        if Path(r['id']).name != r['id'] or r['id'] in ('.', '..'):
            continue
        # Include every retry working copy, not just the last tree recorded by the run.
        for tree in (fdir / 'lane/trees' / r['id']).glob('*'):
            if tree.name.isdecimal():
                yield tree, None, 'lane ' + r['id'], ('lane', r['id']), receipt
    for g in f.groups(fdir).values():
        rerun = g.get('rerun') or {}
        if (g.get('sampled') and not rerun.get('not_agree', [True])
                and set(rerun.get('agree', [])) == set(g['sampled'])
                and (g.get('rerun_dispatched') or '') <= rerun.get('recorded', '')):
            yield (fdir / 'rerun' / g['name'] / 'tree', g['source_revision'],
                   'AGREE rerun ' + g['name'], ('rerun', g['name']), None)
    if prune_claims:
        seen = set()
        for queue in (root / '.local/queue').glob('*/queue.tsv'):
            for unit in f.wq.read_queue(queue.parent):
                for tier in TIERS:
                    tree = root / '.local/worktrees/draft' / (unit['key'] + '-' + tier)
                    if tree not in seen:
                        seen.add(tree)
                        yield tree, None, 'draft ' + unit['key'], ('draft', unit['key']), (queue.parent, unit, tier)


def check_live(fdir, tree, owner, metadata):
    if owner[0] == 'lane':
        f.refuse(finished(lane.read(metadata)), 'receipt is running, queued or awaiting CI')
    if owner[0] == 'rerun':
        current = f.load_group(fdir, owner[1])
        rerun = current.get('rerun') or {}
        f.refuse(not rerun.get('not_agree', [True])
                 and set(rerun.get('agree', [])) == set(current.get('sampled', []))
                 and (current.get('rerun_dispatched') or '') <= rerun.get('recorded', ''),
                 'rerun no longer complete and AGREE')
    for name in ('queue', 'tooling-queue', 'tooling', 'runs'):
        for path in (fdir / 'lane' / name).glob('*.json'):
            value = lane.read(path)
            pending = (value.get('integrated') or {}).get('pushed') and not finished(value)
            if value.get('state') in ('queued', 'running') or pending:
                for key in ('root', 'tree'):
                    if value.get(key):
                        f.refuse(not Path(value[key]).resolve().is_relative_to(tree), 'queued/running input')


def archive_evidence(tree, archive, lane_copy):
    """Clean tracked files remain recoverable from Git; archive private evidence only."""
    tracked = set(f.git(tree, 'ls-files', '-z').split('\0'))
    links = {}
    for directory, dirs, files in os.walk(tree, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                links[str(path.relative_to(tree))] = os.readlink(path)
        dirs[:] = [d for d in dirs if d != '.git' and not (Path(directory) / d).is_symlink()]
        for name in files:
            src = Path(directory) / name
            rel = src.relative_to(tree)
            evidence = (src.suffix.lower() in ('.json', '.jsonl', '.log', '.txt', '.stdout', '.stderr')
                        or any(p in ('handoffs', 'reviews') or 'logs' in p for p in rel.parts[:-1])
                        or lane_copy and src.suffix.lower() in ('.cpp', '.h', '.py'))
            if not src.is_symlink() and str(rel) not in tracked and evidence:
                dest = archive / 'files' / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                if src.stat().st_size <= 8 * 1024 ** 2:
                    shutil.copy2(src, dest)
                else:
                    # Keep large logs without doubling their disk footprint.
                    shutil.move(str(src), dest)
    if lane_copy:
        patch = f.git(tree, 'diff', '--binary', 'HEAD')
        if patch:
            (archive / 'working-changes.patch').write_text(patch)
    lane.write(archive / 'links.json', links)


def cleanup(root, fdir, dry_run=False, prune_claims=False, keep_task_prefixes=()):
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    results = []
    (fdir / 'cleanup').mkdir(parents=True, exist_ok=True)
    # Serialize cleaners, never block an unrelated verifier/publication run.
    with f.wq.locked(fdir / 'cleanup/.cleanup.lock'):
        for tree, commit, proof, owner, metadata in candidates(root, fdir, prune_claims):
            if not tree.exists() or set(p.name for p in tree.iterdir()) == {'.git'}:
                continue
            row = dict(tree=str(tree), proof=proof, removed=False)
            results.append(row)
            reservation = None
            with ExitStack() as locks:
                try:
                    lane_copy = owner[0] == 'lane'
                    if owner[0] == 'draft':
                        f.refuse(not any(owner[1].startswith(p) for p in keep_task_prefixes), 'protected worker task')
                        queue, unit, tier = metadata
                        locks.enter_context(f.wq.locked(f.drafts.task_dir(root, unit) / 'draft-lifecycle.lock'))
                        harvest = claim_harvest(root, queue, unit, tier)
                        f.refuse(harvest.get('tree') == str(tree), 'harvest checkout path mismatch')
                        row['harvest_commit'] = harvest['commit']
                    f.refuse(not tree.is_symlink() and tree.resolve() == tree.absolute(), 'symlink checkout')
                    f.refuse(not (tree / '.git').is_symlink(), 'symlink Git metadata')
                    allowed = root / '.local/worktrees/draft' if owner[0] == 'draft' else fdir
                    f.refuse(tree.is_relative_to(allowed) and tree != allowed and tree != root, 'tree outside lifecycle directory')
                    with lane.state_lock(fdir):
                        check_live(fdir, tree, owner, metadata)
                    f.refuse(Path(f.git(tree, 'rev-parse', '--show-toplevel')).resolve() == tree, 'not a checkout root')
                    if not lane_copy:
                        status = f.git(tree, 'status', '--porcelain', '--untracked-files=all', '--', '.', ':(exclude).local')
                        f.refuse(not status, 'dirty checkout: ' + status[:500])
                        if commit:
                            f.refuse(f.git(tree, 'rev-parse', 'HEAD') == commit, 'checkout differs from completed commit')
                        marker = json.loads((tree / '.local/worktree-owner.json').read_text())
                        f.refuse((marker.get('kind'), marker.get('task')) == owner, 'worktree owner mismatch')
                    for directory, dirs, files in os.walk(tree, followlinks=False):
                        f.refuse(Path(directory) == tree or '.git' not in dirs + files, 'nested checkout')
                        dirs[:] = [d for d in dirs if d != '.git' and not (Path(directory) / d).is_symlink()]
                    if dry_run:
                        row['would_remove'] = True
                        continue
                    reservation = fdir / 'cleanup/claims' / (hashlib.sha256(str(tree).encode()).hexdigest() + '.json')
                    with lane.state_lock(fdir):
                        check_live(fdir, tree, owner, metadata)
                        lane.write(reservation, dict(tree=str(tree), active=True, owner=lane.process_owner()))
                    archive = root / '.local/archive' / 'cleanup' / uuid.uuid4().hex
                    archive.mkdir(parents=True)
                    archive_evidence(tree, archive, lane_copy)
                    lane.write(archive / 'receipt.json', row)
                    if owner[0] == 'draft':
                        harvest = claim_harvest(root, queue, unit, tier)
                        f.refuse(harvest['commit'] == row['harvest_commit'], 'harvest changed during cleanup')
                        f.git(root, 'update-ref', 'refs/cleanup/harvests/' + harvest['commit'], harvest['commit'])
                    with lane.state_lock(fdir):
                        check_live(fdir, tree, owner, metadata)
                    if (tree / '.git').is_file():
                        shutil.copytree(Path(f.git(tree, 'rev-parse', '--absolute-git-dir')), archive / 'registration')
                        f.git(root, 'worktree', 'remove', str(tree))  # no force, branch deletion or prune
                    else:
                        # Other clones may borrow this object store. Keep .git and all its refs.
                        f.refuse((tree / '.git').is_dir(), 'not a Git checkout')
                        for path in tree.iterdir():
                            if path.name != '.git':
                                if path.is_dir() and not path.is_symlink():
                                    shutil.rmtree(path)
                                else:
                                    path.unlink()
                    row.update(removed=True, archive=str(archive))
                    lane.write(archive / 'receipt.json', row)
                except (f.FlowError, OSError, ValueError) as error:
                    row['reason'] = str(error)
                finally:
                    if reservation is not None and reservation.is_file():
                        with lane.state_lock(fdir):
                            value = lane.read(reservation)
                            value['active'] = False
                            lane.write(reservation, value)
    return results
