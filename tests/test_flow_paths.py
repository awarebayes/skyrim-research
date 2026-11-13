"""Bounded Git transport preserves the exact reviewed file selection."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flow


class GitPaths(unittest.TestCase):
    def test_large_status_selection_stays_below_argument_budget(self):
        paths = [f'reconstruction/{"a" * 100}/{"b" * 100}/{"c" * 100}/unit_{n:05}.cpp'
                 for n in range(5000)]
        calls = []

        def status(command, **kwargs):
            selected = command[command.index('--') + 1:]
            self.assertLessEqual(sum(len(p.encode()) + 16 for p in selected), flow.PATHSPEC_ARG_BYTES)
            calls.append(selected)
            return subprocess.CompletedProcess(command, 0, ''.join('?? ' + p + '\0' for p in selected), '')

        with patch.object(flow.subprocess, 'run', side_effect=status):
            self.assertEqual(flow.changed(Path('.'), paths + paths[:3]), sorted(paths))
        self.assertGreater(len(calls), 1)
        self.assertEqual([p for group in calls for p in group], sorted(paths))

    def test_add_transports_all_paths_on_standard_input(self):
        paths = [f'reconstruction/{"a" * 150}/unit_{n}.cpp' for n in range(10000)]
        with patch.object(flow.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            flow.git(Path('.'), 'add', '--', *paths)
        self.assertEqual(run.call_args.args[0], ['git', 'add', '--pathspec-from-file=-', '--pathspec-file-nul'])
        self.assertEqual(run.call_args.kwargs['input'], ''.join(p + '\0' for p in paths))

    def test_add_refuses_embedded_nul_without_running_git(self):
        with patch.object(flow.subprocess, 'run') as run:
            with self.assertRaisesRegex(flow.FlowError, 'NUL'):
                flow.git(Path('.'), 'add', '--', 'safe\0unselected')
        run.assert_not_called()

    def test_cross_batch_magic_refused_before_query(self):
        for exclusion in (':(exclude)group/drop.cpp', ':!group/drop.cpp', ':^group/drop.cpp',
                          ':(top,exclude)group/drop.cpp'):
            with self.subTest(exclusion=exclusion), patch.object(flow, 'PATHSPEC_ARG_BYTES', 48), \
                    patch.object(flow.subprocess, 'run') as run:
                with self.assertRaisesRegex(flow.FlowError, 'magic pathspecs'):
                    flow.changed(Path('.'), ['group', exclusion])
                run.assert_not_called()

    def test_small_global_exclusion_preserved_in_status_and_add(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
            (root / 'group').mkdir()
            for rel in ['group/keep.cpp', 'group/drop.cpp', 'unrelated.cpp']:
                (root / rel).write_text('synthetic\n')
            paths = ['group', ':(exclude)group/drop.cpp']
            self.assertEqual(flow.changed(root, paths), ['group/keep.cpp'])
            flow.git(root, 'add', '--', *paths)
            staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=root, text=True)
            self.assertEqual(staged, 'group/keep.cpp\0')

    def test_real_status_and_add_preserve_unusual_names_and_exclusions(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
            flow.git(root, 'config', 'user.name', 'Synthetic test')
            flow.git(root, 'config', 'user.email', 'test@example.invalid')
            (root / 'deleted.txt').write_text('original\n')
            (root / 'modified.txt').write_text('original\n')
            flow.git(root, 'add', '--', 'deleted.txt', 'modified.txt')
            flow.git(root, 'commit', '--quiet', '-m', 'synthetic baseline')
            (root / 'deleted.txt').unlink()
            (root / 'modified.txt').write_text('changed\n')
            unusual = ['space name.cpp', 'line\nname.cpp', 'quote"name.cpp', 'café.cpp', '-leading.cpp']
            for rel in unusual + ['unselected.cpp']:
                (root / rel).write_text('synthetic\n')
            (root / 'group').mkdir()
            (root / 'group/nested.cpp').write_text('synthetic\n')
            wanted = unusual + ['deleted.txt', 'modified.txt', 'group', 'group/nested.cpp']
            command = ['git', 'status', '--porcelain', '-z', '--no-renames', '--untracked-files=all', '--', *wanted]
            original = subprocess.check_output(command, cwd=root, text=True)
            expected = sorted({entry[3:] for entry in original.split('\0') if len(entry) > 3})
            with patch.object(flow, 'PATHSPEC_ARG_BYTES', 64):
                changed = flow.changed(root, wanted)
            self.assertEqual(changed, expected)
            flow.git(root, 'add', '--', *changed)
            staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=root, text=True)
            self.assertEqual(set(filter(None, staged.split('\0'))), set(expected))
            self.assertNotIn('unselected.cpp', changed)

    def test_later_status_failure_does_not_return_partial_selection(self):
        replies = [subprocess.CompletedProcess([], 0, '?? a\0', ''),
                   subprocess.CompletedProcess([], 1, '', 'synthetic failure')]
        with patch.object(flow, 'PATHSPEC_ARG_BYTES', 17), patch.object(flow.subprocess, 'run', side_effect=replies):
            with self.assertRaisesRegex(flow.FlowError, 'synthetic failure'):
                flow.changed(Path('.'), ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
