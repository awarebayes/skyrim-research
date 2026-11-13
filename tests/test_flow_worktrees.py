import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flow_worktrees as fw


class WorktreeHygiene(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / 'main'
        self.root.mkdir()
        self.git(self.root, 'init', '-b', 'main')
        self.git(self.root, 'config', 'user.email', 'test@example.com')
        self.git(self.root, 'config', 'user.name', 'Test')
        (self.root / 'file').write_text('base')
        self.git(self.root, 'add', 'file')
        self.git(self.root, 'commit', '-m', 'base')
        self.git(self.root, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.fdir = self.root / '.local' / 'flow'

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, root, *args):
        return subprocess.run(['git', '-C', str(root), *args], check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True).stdout

    def tree(self, name):
        path = self.base / name
        self.git(self.root, 'worktree', 'add', '-b', name, str(path), 'main')
        return path

    def age(self, path):
        old = time.time() - 7 * 3600
        for directory, dirs, files in os.walk(path, topdown=False):
            for name in dirs + files:
                os.utime(Path(directory) / name, (old, old), follow_symlinks=False)
            os.utime(directory, (old, old))

    def command(self, action, dry=False):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fw.run(self.root, self.fdir, action, dry)
        return out.getvalue()

    def test_completed_draft_prunes_clean_unmerged_tree_and_preserves_branch(self):
        (self.root / '.gitignore').write_text('.local/\n')
        self.git(self.root, 'add', '.gitignore')
        self.git(self.root, 'commit', '-m', 'ignore private state')
        self.git(self.root, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        queue = self.root / '.local/queue/test'
        queue.mkdir(parents=True)
        directory = self.root / '.local/tasks/g/unit'
        directory.mkdir(parents=True)
        (queue / 'queue.tsv').write_text('.local/tasks/g/unit\ta.cpp\t0x1000\t1\n')
        tree = self.root / '.local/worktrees/draft/unit-first'
        tree.parent.mkdir(parents=True)
        self.git(self.root, 'worktree', 'add', '-b', 'draft/unit-first', str(tree), 'main')
        self.git(tree, 'commit', '--allow-empty', '-m', 'harvest')
        local = tree / '.local'
        local.mkdir()
        (local / 'worktree-owner.json').write_text(json.dumps({'task': 'unit', 'kind': 'draft'}))
        (directory / 'draft-first.json').write_text(json.dumps(
            {'ready': True, 'tree': str(tree), 'branch': 'draft/unit-first'}))
        (queue / 'done').mkdir()
        (queue / 'done/unit.json').write_text('{}')
        self.assertIn('prunable', self.command('list'))
        (tree / 'untracked').write_text('keep')
        self.command('prune')
        self.assertTrue(tree.exists())
        (tree / 'untracked').unlink()
        self.command('prune')
        self.assertFalse(tree.exists())
        self.assertIn('draft/unit-first', self.git(self.root, 'branch', '--list'))
        self.command('prune')
        self.assertIn('draft/unit-first', self.git(self.root, 'branch', '--list'))

    def test_prune_and_dry_run(self):
        clean = self.tree('clean')
        dirty = self.tree('dirty')
        unmerged = self.tree('unmerged')
        locked = self.tree('locked')
        recent = self.tree('recent')
        referenced = self.tree('referenced')
        for path in (clean, dirty, unmerged, locked, referenced):
            self.age(path)
        (dirty / 'new').write_text('dirty')
        self.git(unmerged, 'commit', '--allow-empty', '-m', 'unmerged')
        self.git(self.root, 'worktree', 'lock', str(locked))
        self.fdir.mkdir(parents=True)
        (self.fdir / 'marker').write_bytes(b'\x00/path\x00' + str(referenced).encode())
        self.git(self.root, 'branch', 'merged-branch')
        self.git(self.root, 'branch', 'unmerged-branch', 'unmerged')
        (self.root / 'file').write_text('stash')
        self.git(self.root, 'stash', 'push', '-m', 'keep')
        before = self.git(self.root, 'stash', 'list')
        dry = self.command('prune', True)
        self.assertIn('would remove worktree', dry)
        self.assertTrue(clean.exists())
        self.assertIn('merged-branch', self.git(self.root, 'branch', '--list'))
        output = self.command('prune')
        self.assertFalse(clean.exists())
        for path in (dirty, unmerged, locked, recent, referenced, self.root):
            self.assertTrue(path.exists(), path)
        branches = self.git(self.root, 'branch', '--list')
        self.assertNotIn('merged-branch', [line.strip().lstrip('+* ').strip() for line in branches.splitlines()])
        self.assertNotIn('clean\n', branches)
        self.assertIn('unmerged-branch', branches)
        self.assertEqual(before, self.git(self.root, 'stash', 'list'))
        for reason in ('dirty', 'unmerged', 'locked', 'recently modified', 'main checkout', 'flow state reference'):
            self.assertIn(reason, output)
        self.assertIn('stash', self.command('list'))


if __name__ == '__main__':
    unittest.main()
