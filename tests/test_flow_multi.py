"""Synthetic multi-group integration, including refusal and resume paths."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_flow import Repo, FUNCS, git, flow, github_claims


class MultiGroupIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = Repo(self.tmp)
        self.root, self.fdir = self.repo.root, self.repo.fdir
        for name, kwargs in [('claims.sync_safe', {}),
                             ('claims.cached', {'return_value': (github_claims.ClaimIndex(), None)})]:
            mock = patch(name, **kwargs)
            mock.start()
            self.addCleanup(mock.stop)
        self.names = flow.review_group(self.root, self.fdir, max_size=2)
        self.assertEqual(len(self.names), 2)
        for name in self.names:
            group = flow.load_group(self.fdir, name)
            blocks = [(r, size, self.repo.digest(r), 'approve', 'none') for r, size, _ in FUNCS
                      if hex(r) in group['functions']]
            self.repo.save_review(group['task_id'], blocks)
            self.repo.save_review(group['task_id'] + '-s',
                                  [b for b in blocks if hex(b[0]) in group['sampled']], sampling='yes')
            compare = self.tmp / (name + '.txt')
            compare.write_text(''.join(r + ' AGREE\n' for r in group['sampled']))
            flow.record_rerun(self.root, self.fdir, name, compare)

    def integrate(self, **kwargs):
        return flow.integrate_groups(self.root, self.fdir, self.names, 'synthetic-combined',
                                     python=sys.executable, ci_wait=0, **kwargs)

    def test_one_commit_preserves_reviews_and_records_every_group(self):
        old = git(self.repo.origin, 'rev-parse', 'main')
        reviews = {p: p.read_bytes() for p in (self.root / '.local/reviews').glob('*.md')}
        (self.root / 'reconstruction/x/Unrelated.cpp').write_text('int untouched;\n')
        with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
            result = self.integrate()
        integ = result['integrated']
        self.assertEqual(checks.call_count, 1)
        self.assertEqual(integ['accepted'], 3)
        self.assertEqual(integ['ci'], 'green')
        self.assertEqual(git(self.repo.origin, 'rev-list', '--count', old + '..main'), '1')
        data = json.loads(git(self.root, 'show', integ['commit'] + ':data/progress.json'))
        self.assertTrue(all(fn['status'] == 'matched' for fn in data['functions']))
        self.assertNotIn('Unrelated.cpp', git(self.root, 'show', '--stat', integ['commit']))
        for name in self.names:
            group = flow.load_group(self.fdir, name)
            self.assertEqual(group['integrated']['commit'], integ['commit'])
            self.assertEqual(group['integrated']['accepted'], len(group['functions']))
            self.assertEqual(group['integrated']['ci'], 'green')
        self.assertEqual(reviews, {p: p.read_bytes() for p in reviews})
        self.assertEqual(set(integ['wall_seconds']), {'build', 'checks', 'push', 'ci'})
        self.assertTrue(all(v >= 0 for v in integ['wall_seconds'].values()))

    def test_missing_later_review_never_commits_or_pushes(self):
        group = flow.load_group(self.fdir, self.names[-1])
        flow.review_path(self.root, group).unlink()
        old = git(self.repo.origin, 'rev-parse', 'main')
        with self.assertRaises(flow.FlowError):
            self.integrate()
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), old)
        self.assertTrue(all(flow.load_group(self.fdir, n).get('integrated') is None for n in self.names))

    def test_later_sampling_disagreement_never_commits_or_pushes(self):
        group = flow.load_group(self.fdir, self.names[-1])
        self.repo.save_review(group['task_id'] + '-s',
                              [(r, size, self.repo.digest(r), 'reject', 'none') for r, size, _ in FUNCS
                               if hex(r) in group['sampled']], sampling='yes')
        old = git(self.repo.origin, 'rev-parse', 'main')
        with self.assertRaisesRegex(flow.FlowError, 'sampling gate'):
            self.integrate()
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), old)

    def test_later_acceptance_failure_never_commits_or_pushes(self):
        group = flow.load_group(self.fdir, self.names[-1])
        p = self.root / 'tools/accept_function.py'
        p.write_text(p.read_text().replace("data = json.loads", "if '" + group['task_id'] + "' in review: raise SystemExit(9)\ndata = json.loads", 1))
        git(self.root, 'add', 'tools/accept_function.py')
        git(self.root, 'commit', '--quiet', '-m', 'synthetic late refusal')
        git(self.root, 'push', '--quiet', 'origin', 'main')
        old = git(self.repo.origin, 'rev-parse', 'main')
        with self.assertRaisesRegex(flow.FlowError, 'accept_function.py'):
            self.integrate()
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), old)
        self.assertTrue(all(flow.load_group(self.fdir, n).get('integrated') is None for n in self.names))

    def test_red_ci_resumes_same_commit_without_another_push(self):
        p = self.root / 'tools/ci_status.py'
        p.write_text("from pathlib import Path\nimport sys\nsys.exit(0 if (Path('.local') / 'ci-ok').exists() else 1)\n")
        git(self.root, 'add', 'tools/ci_status.py')
        git(self.root, 'commit', '--quiet', '-m', 'synthetic CI state')
        git(self.root, 'push', '--quiet', 'origin', 'main')
        with self.assertRaisesRegex(flow.FlowError, 'CI RED'):
            self.integrate()
        first = flow.load_group(self.fdir, self.names[0])['integrated']
        (self.root / '.local/ci-ok').write_text('yes')
        result = self.integrate()['integrated']
        self.assertEqual(result['commit'], first['commit'])
        self.assertEqual(result['pushed'], first['pushed'])
        self.assertEqual(result['ci'], 'green')

    def test_integrated_check_failure_never_pushes(self):
        p = self.root / 'tools/check.py'
        p.write_text("import sys\nsys.exit(0 if '--staged' in sys.argv else 8)\n")
        git(self.root, 'add', 'tools/check.py')
        git(self.root, 'commit', '--quiet', '-m', 'synthetic integrated check refusal')
        git(self.root, 'push', '--quiet', 'origin', 'main')
        old = git(self.repo.origin, 'rev-parse', 'main')
        with self.assertRaisesRegex(flow.FlowError, 'check.py'):
            self.integrate()
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), old)
        for name in self.names:
            integ = flow.load_group(self.fdir, name)['integrated']
            self.assertIsNone(integ['checks'])
            self.assertIsNone(integ['pushed'])

    def test_origin_advance_replays_selection_and_rechecks_new_tree(self):
        original_check = flow.pre_push_checks
        checked = []

        def advance(root, commit, python):
            original_check(root, commit, python)
            checked.append(commit)
            if len(checked) == 1:
                other = self.tmp / 'other'
                subprocess.run(['git', 'clone', '--quiet', '--branch', 'main',
                                str(self.repo.origin), str(other)], check=True)
                git(other, 'config', 'user.email', 'test@example.invalid')
                git(other, 'config', 'user.name', 'test')
                (other / 'unrelated.txt').write_text('concurrent change\n')
                path = other / 'data/progress.json'
                incoming = json.loads(path.read_text())
                incoming['functions'].append({'id': 'synthetic-build-0x3000', 'build_id': 'synthetic-build',
                                              'rva': 0x3000, 'size': 8, 'status': 'mapped', 'name': 'Concurrent::Extra'})
                path.write_text(json.dumps(incoming, indent=2) + '\n')
                git(other, 'add', 'unrelated.txt', 'data/progress.json')
                git(other, 'commit', '--quiet', '-m', 'advance origin')
                git(other, 'push', '--quiet', 'origin', 'main')

        with patch.object(flow, 'pre_push_checks', side_effect=advance):
            result = self.integrate()
        self.assertEqual(len(checked), 2)
        self.assertNotEqual(checked[0], checked[1])
        self.assertEqual(result['integrated']['ci'], 'green')
        self.assertEqual(len(result['unpublished_attempts']), 1)
        self.assertIsNone(result['unpublished_attempts'][0]['pushed'])
        commit = result['integrated']['commit']
        self.assertEqual(git(self.root, 'show', commit + ':unrelated.txt'), 'concurrent change')
        data = json.loads(git(self.root, 'show', commit + ':data/progress.json'))
        self.assertTrue(all(fn['status'] == 'matched' for fn in data['functions'] if fn['rva'] != 0x3000))
        self.assertEqual(next(fn for fn in data['functions'] if fn['rva'] == 0x3000)['name'], 'Concurrent::Extra')

    def test_replay_refuses_concurrent_carried_file(self):
        original_check = flow.pre_push_checks

        def advance(root, commit, python):
            original_check(root, commit, python)
            other = self.tmp / 'overlap'
            subprocess.run(['git', 'clone', '--quiet', '--branch', 'main',
                            str(self.repo.origin), str(other)], check=True)
            git(other, 'config', 'user.email', 'test@example.invalid')
            git(other, 'config', 'user.name', 'test')
            changed = 'reconstruction/x/Foo.cpp'
            (other / changed).write_text('int concurrent;\n')
            git(other, 'add', changed)
            git(other, 'commit', '--quiet', '-m', 'concurrent overlap')
            git(other, 'push', '--quiet', 'origin', 'main')

        with patch.object(flow, 'pre_push_checks', side_effect=advance):
            with self.assertRaisesRegex(flow.FlowError, 'origin changed carried files'):
                self.integrate()
        self.assertEqual(git(self.root, 'show', 'origin/main:reconstruction/x/Foo.cpp'), 'int concurrent;')
        self.assertIsNone(flow.load_group(self.fdir, self.names[0])['integrated']['pushed'])

    def test_replay_refuses_concurrent_selected_entry(self):
        original_check = flow.pre_push_checks

        def advance(root, commit, python):
            original_check(root, commit, python)
            other = self.tmp / 'entry-overlap'
            subprocess.run(['git', 'clone', '--quiet', '--branch', 'main',
                            str(self.repo.origin), str(other)], check=True)
            git(other, 'config', 'user.email', 'test@example.invalid')
            git(other, 'config', 'user.name', 'test')
            path = other / 'data/progress.json'
            data = json.loads(path.read_text())
            data['functions'][0]['name'] = 'Concurrent::Name'
            path.write_text(json.dumps(data, indent=2) + '\n')
            git(other, 'add', 'data/progress.json')
            git(other, 'commit', '--quiet', '-m', 'concurrent selected entry')
            git(other, 'push', '--quiet', 'origin', 'main')

        with patch.object(flow, 'pre_push_checks', side_effect=advance):
            with self.assertRaisesRegex(flow.FlowError, 'origin changed selected inventory entries'):
                self.integrate()
        data = json.loads(git(self.root, 'show', 'origin/main:data/progress.json'))
        self.assertEqual(data['functions'][0]['name'], 'Concurrent::Name')
        self.assertIsNone(flow.load_group(self.fdir, self.names[0])['integrated']['pushed'])

    def test_initial_behind_checkout_refuses_overlapping_origin_change(self):
        other = self.tmp / 'initial-overlap'
        subprocess.run(['git', 'clone', '--quiet', '--branch', 'main',
                        str(self.repo.origin), str(other)], check=True)
        git(other, 'config', 'user.email', 'test@example.invalid')
        git(other, 'config', 'user.name', 'test')
        (other / 'reconstruction/x/Foo.cpp').write_text('int earlier_concurrent;\n')
        git(other, 'add', 'reconstruction/x/Foo.cpp')
        git(other, 'commit', '--quiet', '-m', 'origin ahead before integration')
        git(other, 'push', '--quiet', 'origin', 'main')
        head = git(self.repo.origin, 'rev-parse', 'main')
        with self.assertRaisesRegex(flow.FlowError, 'origin changed carried files'):
            self.integrate()
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), head)
        self.assertTrue(all(flow.load_group(self.fdir, n).get('integrated') is None for n in self.names))

    def test_batch_resume_requires_all_groups_and_next_actions_lists_it_once(self):
        self.integrate(push=False)
        with self.assertRaisesRegex(flow.FlowError, 'resume combined integration'):
            flow.integrate(self.root, self.fdir, self.names[0], push=False)
        actions = flow.next_actions(self.root, self.fdir, online=False)
        combined = [text for kind, text in actions if 'integrate-groups' in text]
        self.assertEqual(len(combined), 1)
        self.assertTrue(all(name in combined[0] for name in self.names))

    def test_changed_saved_review_refuses_resume(self):
        self.integrate(push=False)
        group = flow.load_group(self.fdir, self.names[0])
        p = flow.review_path(self.root, group)
        p.write_text(p.read_text().replace('reasons: synthetic', 'reasons: synthetic additional context'))
        with self.assertRaisesRegex(flow.FlowError, 'saved review changed'):
            self.integrate()


if __name__ == '__main__':
    unittest.main()
