"""Read-only worktree inventory and conservative cleanup."""
import datetime as dt
import os
import re
from pathlib import Path
import subprocess
import time


def git(root, *args, check=True):
    return subprocess.run(['git', '-C', str(root), *args], text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=check, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})


def raise_walk_error(error):
    raise error


def disk_info(path):
    size = 0
    latest = path.stat().st_mtime
    for directory, dirs, files in os.walk(path, followlinks=False, onerror=raise_walk_error):
        for name in dirs + files:
            try:
                stat = (Path(directory) / name).lstat()
                latest = max(latest, stat.st_mtime)
                size += stat.st_size if not (Path(directory) / name).is_symlink() else 0
            except FileNotFoundError:
                continue
    return size, latest


def in_use(path, fdir, original):
    # Treat flow-managed trees and explicit path references as in use.
    if path == fdir or fdir in path.parents:
        return True
    if not fdir.is_dir():
        return False
    needles = {str(path), str(original), os.path.relpath(path, fdir.parent.parent)}
    for file in fdir.rglob('*'):
        if not file.is_file() or file.is_symlink():
            continue
        try:
            content = file.read_text(errors='replace')
            if any(n in content for n in needles):
                return True
            for token in re.findall(r'[^\s"\'<>]+', content):
                if token.startswith('/') and Path(token).resolve() == path:
                    return True
        except OSError:
            return True
    return False


def inventory(root, fdir):
    raw = git(root, 'worktree', 'list', '--porcelain', '-z').stdout
    records = []
    main_path = Path(raw.split('\0', 1)[0].removeprefix('worktree ')).resolve()
    flow_dirs = {fdir, main_path / '.local' / 'flow'}
    for block in raw.split('\0\0'):
        if not block.strip('\0'):
            continue
        fields = dict(item.split(' ', 1) if ' ' in item else (item, '')
                      for item in block.strip('\0').split('\0'))
        path = Path(fields['worktree']).resolve()
        reasons = []
        if not records:
            reasons.append('main checkout')
        if 'locked' in fields:
            reasons.append('locked')
        status = git(path, 'status', '--porcelain=v1', '-z', '--untracked-files=all', check=False)
        if status.returncode:
            reasons.append('status unavailable')
            modified = untracked = 0
        else:
            entries = status.stdout.split('\0')
            modified = untracked = 0
            i = 0
            while i < len(entries) and entries[i]:
                entry = entries[i]
                if entry.startswith('??'):
                    untracked += 1
                else:
                    modified += 1
                    if 'R' in entry[:2] or 'C' in entry[:2]:
                        i += 1
                i += 1
            if modified or untracked:
                reasons.append('dirty')
        head = fields.get('HEAD', '')
        merged = bool(head) and git(root, 'merge-base', '--is-ancestor', head, 'origin/main', check=False).returncode == 0
        if not merged:
            reasons.append('unmerged')
        counts = git(root, 'rev-list', '--left-right', '--count', f'{head}...origin/main').stdout.split()
        try:
            size, modified_at = disk_info(path)
            if time.time() - modified_at < 6 * 3600:
                reasons.append('recently modified')
        except OSError:
            size, modified_at = 0, 0
            reasons.append('directory unavailable')
        if any(in_use(path, directory, Path(fields['worktree'])) for directory in flow_dirs):
            reasons.append('flow state reference')
        records.append(dict(path=path, branch=fields.get('branch', '').removeprefix('refs/heads/') or '(detached)',
                            head=head, ahead=int(counts[0]), behind=int(counts[1]), modified=modified,
                            untracked=untracked, merged=merged, size=size, mtime=modified_at, reasons=reasons))
    checked = {r['branch'] for r in records}
    branches = []
    for name in git(root, 'for-each-ref', '--format=%(refname:short)', 'refs/heads').stdout.splitlines():
        if name in checked:
            continue
        merged = git(root, 'merge-base', '--is-ancestor', name, 'origin/main', check=False).returncode == 0
        ahead = int(git(root, 'rev-list', '--count', f'origin/main..{name}').stdout)
        branches.append(dict(name=name, merged=merged, ahead=ahead))
    stashes = git(root, 'stash', 'list', '--format=%gd%x09%gs%x09%ci').stdout.splitlines()
    return records, branches, stashes


def display_path(path, root):
    try:
        return str(path.relative_to(Path(root).resolve())) or '.'
    except ValueError:
        return str(path)


def run(root, fdir, action, dry_run=False):
    root, fdir = Path(root).resolve(), Path(fdir).resolve()
    trees, branches, stashes = inventory(root, fdir)
    prunable = [t for t in trees if not t['reasons']]
    # Branches of removable trees become eligible after their worktrees are removed.
    candidates = branches + [dict(name=t['branch'], merged=True, ahead=0) for t in prunable
                             if t['branch'] != '(detached)']
    deletable = [b for b in candidates if b['merged']]
    branch_total = len(branches) + sum(t['branch'] != '(detached)' for t in trees)
    if action == 'list':
        for t in trees:
            stamp = dt.datetime.fromtimestamp(t['mtime'], dt.timezone.utc).isoformat()
            print(f"worktree {display_path(t['path'], root)} | {t['branch']} | {t['head'][:12]} | "
                  f"ahead {t['ahead']} behind {t['behind']} | {'dirty' if t['modified'] or t['untracked'] else 'clean'} "
                  f"(modified {t['modified']}, untracked {t['untracked']}) | merged {'yes' if t['merged'] else 'no'} | "
                  f"modified {stamp} | size {t['size']} bytes | "
                  f"{'needs a decision: ' + ', '.join(t['reasons']) if t['reasons'] else 'prunable'}")
        for b in branches:
            print(f"branch {b['name']} | merged {'yes' if b['merged'] else 'no'} | ahead {b['ahead']}")
        for stash in stashes:
            print('stash ' + stash)
    else:
        print('needs a decision:')
        for t in trees:
            if t['reasons']:
                print(f"  {display_path(t['path'], root)}: {', '.join(t['reasons'])}")
        for b in branches:
            if not b['merged']:
                print(f"  branch {b['name']}: unmerged")
        for stash in stashes:
            print('  stash ' + stash)
        reclaimed = 0
        removed = 0
        for t in prunable:
            print(f"{'would remove' if dry_run else 'remove'} worktree {display_path(t['path'], root)}")
            if not dry_run:
                git(root, 'worktree', 'remove', str(t['path']))
                reclaimed += t['size']
                removed += 1
        deleted = 0
        for b in deletable:
            print(f"{'would delete' if dry_run else 'delete'} branch {b['name']}")
            if not dry_run:
                git(root, '-c', f"branch.{b['name']}.remote=origin",
                    '-c', f"branch.{b['name']}.merge=refs/heads/main", 'branch', '-d', '--', b['name'])
                deleted += 1
        if not dry_run:
            print(f'before/after: worktrees {len(trees)}/{len(trees)-removed}; '
                  f'branches {branch_total}/{branch_total-deleted}; '
                  f'stashes {len(stashes)}/{len(stashes)}; reclaimed {reclaimed} bytes')
    print(f'summary: worktrees {len(trees)}, prunable {len(prunable)}, needs-decision {len(trees)-len(prunable)}; '
          f'branches {branch_total} total, {len(branches)} unchecked-out, deletable {len(deletable)} including prunable worktrees; '
          f'stashes {len(stashes)}')
