"""Explicit lifecycle cleanup: preserve evidence, Git refs and stashes, and active/dirty trees."""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

import flow as f
import flow_lane as lane


def candidates(root, fdir):
    for p in (fdir / 'lane/runs').glob('*.json'):
        r = lane.read(p)
        i = r.get('integrated') or {}
        if r['state'] == 'done' and i.get('pushed') and i.get('ci') == 'green' and r.get('tree'):
            tree = Path(r['tree'])
            if tree.parent == fdir / 'lane/trees' / r['id'] and tree.name.isdecimal():
                yield tree, i['commit'], 'green lane ' + r['id'], None, None
    for g in f.groups(fdir).values():
        rerun = g.get('rerun') or {}
        if g.get('sampled') and not rerun.get('not_agree', [True]) and set(rerun.get('agree', [])) == set(g['sampled']):
            if g.get('rerun_dispatched') and g['rerun_dispatched'] > rerun.get('recorded', ''):
                continue
            yield fdir / 'rerun' / g['name'] / 'tree', g['source_revision'], 'AGREE rerun ' + g['name'], ('rerun', g['name']), None
    for queue in (root / '.local/queue').glob('*/queue.tsv'):
        for unit in f.wq.read_queue(queue.parent):
            directory = f.drafts.task_dir(root, unit)
            h = f.drafts.read(directory / 'harvest.json', {})
            if not h.get('commit') or not h.get('tree') or h.get('tier') not in ('first', 'fallback', 'strong'):
                continue
            if any((f.wq.tier_dir(queue.parent, 'claims', tier) / (unit['key'] + '.lock')).exists()
                   for tier in ('first', 'fallback', 'strong')):
                continue
            expected = root / '.local/worktrees/draft' / (unit['key'] + '-' + h['tier'])
            if Path(h['tree']) == expected and f.git(root, 'rev-parse', '--verify',
                                                    f"refs/harvests/{unit['key']}/{h['tier']}", check=False) == h['commit']:
                yield expected, h['commit'], 'harvested ' + unit['key'], ('draft', unit['key']), directory / 'draft-lifecycle.lock'


def cleanup(root, fdir, dry_run=False):
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    results = []
    with lane.lane_lock(fdir):
        with lane.state_lock(fdir):
            active = [lane.read(p) for p in (fdir / 'lane/queue').glob('*.json')
                      if lane.read(p)['state'] in ('queued', 'running')]
            active += [lane.read(p) for p in (fdir / 'lane/tooling-queue').glob('*.json')
                       if lane.read(p)['state'] in ('queued', 'running')]
            active += [lane.read(p) for p in (fdir / 'lane/tooling').glob('*.json')
                       if lane.read(p)['state'] == 'running']
        for tree, commit, proof, owner, lifecycle_lock in candidates(root, fdir):
            if not tree.exists():
                continue
            row = dict(tree=str(tree), proof=proof, removed=False)
            results.append(row)
            locks = ExitStack()
            reservation = None
            try:
                if lifecycle_lock:
                    locks.enter_context(f.wq.locked(lifecycle_lock))
                    key = owner[1]
                    f.refuse(not any(p.name == key + '.lock' for p in (root / '.local/queue').glob('*/claims*/*.lock')),
                             'draft claim is active')
                expected = tree.absolute()
                f.refuse(not tree.is_symlink() and tree.resolve() == expected, 'symlink checkout')
                f.refuse(not (tree / '.git').is_symlink(), 'symlink Git metadata')
                allowed = root / '.local/worktrees/draft' if owner and owner[0] == 'draft' else fdir
                f.refuse(tree.is_relative_to(allowed) and tree != allowed and tree != root, 'tree outside lifecycle directory')
                f.refuse(not any(Path(i['root']).resolve().is_relative_to(tree) for i in active), 'queued/running input')
                f.refuse(Path(f.git(tree, 'rev-parse', '--show-toplevel')).resolve() == tree, 'not a checkout root')
                status = f.git(tree, 'status', '--porcelain', '--untracked-files=all')
                f.refuse(not status, 'dirty checkout: ' + status[:500])
                if commit:
                    f.refuse(f.git(tree, 'rev-parse', 'HEAD') == commit, 'checkout differs from completed commit')
                if owner:
                    marker = json.loads((tree / '.local/worktree-owner.json').read_text())
                    f.refuse((marker.get('kind'), marker.get('task')) == owner, 'worktree owner mismatch')
                nested = []
                for directory, dirs, files in os.walk(tree, followlinks=False):
                    if Path(directory) != tree and ('.git' in dirs or '.git' in files):
                        nested.append(directory)
                    dirs[:] = [d for d in dirs if d != '.git' and not (Path(directory) / d).is_symlink()]
                f.refuse(not nested, 'nested checkout')
                if dry_run:
                    row['would_remove'] = True
                    continue
                # Close the enqueue/check/remove race without holding state locks during I/O.
                reservation = fdir / 'cleanup/claims' / (hashlib.sha256(str(tree).encode()).hexdigest() + '.json')
                with lane.state_lock(fdir):
                    queued = [lane.read(p) for name in ('queue', 'tooling-queue')
                              for p in (fdir / 'lane' / name).glob('*.json')]
                    f.refuse(not any(i['state'] in ('queued', 'running') and
                                     Path(i['root']).resolve().is_relative_to(tree) for i in queued), 'new queued input')
                    if owner and owner[0] == 'rerun':
                        current = f.load_group(fdir, owner[1])
                        rerun = current.get('rerun') or {}
                        f.refuse(not rerun.get('not_agree', [True]) and
                                 set(rerun.get('agree', [])) == set(current.get('sampled', [])) and
                                 (current.get('rerun_dispatched') or '') <= rerun.get('recorded', ''),
                                 'rerun no longer complete and AGREE')
                    lane.write(reservation, dict(tree=str(tree), active=True, owner=lane.process_owner()))
                archive = fdir / 'cleanup' / uuid.uuid4().hex
                archive.mkdir(parents=True)
                links = {}
                for directory, dirs, files in os.walk(tree, followlinks=False):
                    for name in dirs + files:
                        path = Path(directory) / name
                        if path.is_symlink():
                            links[str(path.relative_to(tree))] = os.readlink(path)
                    dirs[:] = [d for d in dirs if d != '.git' and not (Path(directory) / d).is_symlink()]
                    for name in files:
                        src = Path(directory) / name
                        evidence = any(s.lower() in ('.json', '.jsonl', '.log', '.txt', '.stdout', '.stderr') for s in src.suffixes)
                        if not src.is_symlink() and (evidence or any('logs' in part for part in src.relative_to(tree).parts[:-1])):
                            dest = archive / 'files' / src.relative_to(tree)
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src, dest)
                lane.write(archive / 'links.json', links)
                lane.write(archive / 'receipt.json', row)
                if (tree / '.git').is_file():
                    shutil.copytree(Path(f.git(tree, 'rev-parse', '--absolute-git-dir')), archive / 'registration')
                    f.git(root, 'worktree', 'remove', str(tree))  # no force, branch deletion or prune
                else:
                    # A lane candidate is a shared-object clone. Keep .git at its original
                    # path: other clones may borrow its object store; all refs/stashes survive.
                    f.refuse((tree / '.git').is_dir(), 'not a Git checkout')
                    for path in tree.iterdir():
                        if path.name == '.git':
                            continue
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
                locks.close()
    return results
