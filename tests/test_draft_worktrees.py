"""Synthetic repository tests for draft isolation, harvest refusal and immutable transport."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import draft_worktrees as drafts
import work_queue as wq
import flow
import synthetic_pecoff as fx
from source_digest import include_closure, tu_digest
from test_flow import Repo, BUILD, git


class DraftWorktrees(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.repo = Repo(self.tmp)
        self.root = self.repo.root
        self.q = self.root / '.local/queue/mid'
        self.q.mkdir(parents=True)
        self.unit = {'dir': '.local/tasks/g/g-foo', 'key': 'g-foo',
                     'sources': ['reconstruction/x/Foo.h', 'reconstruction/x/Foo.cpp'],
                     'functions': ['0x1000', '0x1010'], 'budget': 3}
        (self.q / 'queue.tsv').write_text('\t'.join((self.unit['dir'], ','.join(self.unit['sources']),
                                                    ','.join(self.unit['functions']), '3')) + '\n')
        self.directory = self.root / self.unit['dir']
        self.directory.mkdir(parents=True)
        drafts.save(self.directory / 'task.json', {
            'compiled': self.unit['sources'][-1], 'build_id': BUILD, 'max_attempts': 3,
            'functions': [{'rva': '0x1000', 'size': 16, 'symbol': fx.FUNCTION},
                          {'rva': '0x1010', 'size': 8, 'symbol': 'FailedAddition'}]})
        drafts.save(self.directory / 'symbols.json', {'symbols': {}})
        self.claims = patch('claims.project_claims', return_value=({}, None))
        self.claims.start()
        self.addCleanup(self.claims.stop)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def claim(self, tier='first'):
        return wq.claim(self.q, 'worker-' + tier, profile='claude-low', tier=tier)

    def clean_attempt(self, command, cwd=None, **kwargs):
        if str(command[1]).endswith('/tools/verifier/attempt'):
            directory = Path(command[2])
            task = drafts.read(directory / 'task.json')
            dest = directory / 'attempts/001'
            dest.mkdir(parents=True)
            digest = tu_digest(cwd, include_closure(cwd, task['compiled']))
            drafts.save(dest / 'result.json', {'source_revision': digest})
            (dest / 'candidate.obj').write_bytes(fx.coff_object())
            for fn in task['functions']:
                drafts.save(dest / f'0x{int(str(fn["rva"]), 0):x}/report.json', {'result': 'pass'})
            return subprocess.CompletedProcess(command, 0, 'all pass\n', '')
        return self.real_run(command, cwd=cwd, **kwargs)

    def finish(self, tier='first', passed=True):
        records = [json.dumps({'rva': '0x1000', 'result': 'pass' if passed else 'fail'}),
                   json.dumps({'rva': '0x1010', 'result': 'fail'}), json.dumps({'unit': 'Foo'})]
        self.real_run = subprocess.run
        with patch('draft_worktrees.subprocess.run', side_effect=self.clean_attempt):
            return wq.finish(self.q, self.unit['dir'], records, tier=tier)

    def test_claim_is_private_labelled_and_resumes_without_changing_shared_source(self):
        src = self.root / self.unit['sources'][-1]
        src.write_text('shared unfinished work\n')
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        self.assertEqual((tree / self.unit['sources'][-1]).read_text(), 'int a;\n')
        self.assertEqual((tree / '.local/tasks').resolve(), (self.root / '.local/tasks').resolve())
        self.assertEqual(drafts.read(tree / '.local/worktree-owner.json')['task'], 'g-foo')
        self.assertEqual(self.claim()['draft'], unit['draft'])
        with self.assertRaisesRegex(ValueError, 'claimed draft checkout'):
            drafts.route_attempt(self.directory, self.root)
        drafts.route_attempt(self.directory, tree)
        with self.assertRaisesRegex(ValueError, 'clean harvested snapshot'):
            drafts.harvest_for_confirmation(self.directory)
        self.assertEqual(src.read_text(), 'shared unfinished work\n')

    def test_harvest_commits_only_unit_and_carries_snapshot_to_later_tier(self):
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('int harvested;\n')
        self.finish()
        harvest = drafts.current(self.root, self.unit)
        self.assertEqual(harvest['passing'], [0x1000])
        self.assertEqual(git(tree, 'diff-tree', '--no-commit-id', '--name-only', '-r', harvest['commit']),
                         self.unit['sources'][-1])
        (tree / self.unit['sources'][-1]).write_text('int later_dirty;\n')
        fallback = self.claim('fallback')
        other = Path(fallback['draft']['tree'])
        self.assertEqual((other / self.unit['sources'][-1]).read_text(), 'int harvested;\n')
        self.assertEqual(git(other, 'rev-parse', 'HEAD'), git(self.root, 'rev-parse', 'origin/main'))
        self.assertEqual(drafts.read(Path(harvest['task']) / 'task.json')['functions'][0]['rva'], '0x1000')

    def test_clean_attempt_failure_has_no_harvest_or_done_marker(self):
        self.claim()
        with patch('draft_worktrees.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'failed')):
            with self.assertRaisesRegex(wq.QueueError, 'clean harvest attempt failed'):
                wq.finish(self.q, self.unit['dir'], ['{"rva":"0x1000","result":"pass"}'])
        self.assertIsNone(drafts.current(self.root, self.unit))
        self.assertFalse((self.q / 'done/g-foo.json').exists())
        self.assertTrue((self.q / 'claims/g-foo.lock').exists())
        self.assertTrue((self.directory / 'harvest-error-first.json').exists())

    def test_setup_link_and_label_failures_roll_back_and_next_claim_recovers(self):
        for stage in ('link_private', 'label'):
            with self.subTest(stage=stage), patch.object(drafts, stage, side_effect=OSError('injected')):
                with self.assertRaisesRegex(wq.QueueError, 'rolled back'):
                    self.claim()
            self.assertFalse((self.q / 'claims/g-foo.lock').exists())
            self.assertFalse((self.directory / 'draft-first.json').exists())
            self.assertEqual(git(self.root, 'branch', '--list', 'draft/*'), '')
        self.assertTrue(Path(self.claim()['draft']['tree']).is_dir())

    def test_interrupted_setup_claim_recovers_without_becoming_a_legacy_claim(self):
        self.q.joinpath('claims').mkdir()
        wq.try_create(self.q / 'claims/g-foo.lock', 'worker-first', wq.now(), 'claude-low')
        tree = self.root / '.local/worktrees/draft/g-foo-first'
        branch = 'draft/g-foo-first'
        drafts.save(self.directory / 'draft-first.json', {'ready': False, 'tree': str(tree), 'branch': branch})
        git(self.root, 'worktree', 'add', '-b', branch, str(tree), 'origin/main')
        unit = self.claim()
        self.assertTrue(unit['draft']['ready'])
        self.assertTrue((tree / '.local/worktree-owner.json').is_file())
        self.assertTrue((tree / '.local/tasks').is_symlink())

    def test_interruption_before_setup_state_is_written_still_creates_private_checkout(self):
        self.q.joinpath('claims').mkdir()
        wq.try_create(self.q / 'claims/g-foo.lock', 'worker-first', wq.now(), 'claude-low')
        self.assertTrue(Path(self.claim()['draft']['tree']).is_dir())

    def test_setup_overlay_failure_rolls_back_private_inputs_and_checkout(self):
        self.claim()
        self.finish()
        before = (self.directory / 'task.json').read_bytes()
        with patch.object(drafts, 'copy_commit', side_effect=ValueError('injected')):
            with self.assertRaisesRegex(wq.QueueError, 'rolled back'):
                self.claim('fallback')
        self.assertEqual((self.directory / 'task.json').read_bytes(), before)
        self.assertFalse((self.directory / 'draft-fallback.json').exists())
        self.assertTrue(Path(self.claim('fallback')['draft']['tree']).is_dir())

    def test_setup_skeleton_failure_rolls_back_and_retry_completes_setup(self):
        git(self.root, 'rm', *self.unit['sources'])
        git(self.root, 'commit', '-m', 'synthetic missing unit')
        git(self.root, 'push', 'origin', 'main')
        import unit_skeleton
        with patch.object(unit_skeleton, 'write_skeleton', side_effect=unit_skeleton.SkeletonError('injected')):
            with self.assertRaisesRegex(wq.QueueError, 'rolled back'):
                self.claim()
        self.assertEqual(git(self.root, 'branch', '--list', 'draft/*'), '')
        self.assertFalse((self.directory / 'draft-first.json').exists())

        def skeleton(directory, repo):
            for name in self.unit['sources']:
                p = repo / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('// synthetic skeleton\n')

        with patch.object(unit_skeleton, 'write_skeleton', side_effect=skeleton):
            unit = self.claim()
        self.assertTrue((Path(unit['draft']['tree']) / self.unit['sources'][-1]).is_file())

    def test_leftover_failed_definition_refuses_harvest(self):
        self.claim()
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, 'FailedAddition': 2}):
            with self.assertRaisesRegex(wq.QueueError, 'remove failed additions'):
                self.finish()
        self.assertIsNone(drafts.current(self.root, self.unit))

    def test_optimized_out_failed_body_and_overload_refuse_harvest(self):
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        for body in ('static int FailedAddition() { return 1; }',
                     'int SyntheticSum(int other) { return other; }'):
            with self.subTest(body=body):
                (tree / self.unit['sources'][-1]).write_text('int SyntheticSum() { return 0; }\n' + body + '\n')
                with self.assertRaisesRegex(wq.QueueError, 'source contains bodies without passing attempts'):
                    self.finish()
        (tree / self.unit['sources'][-1]).write_text('int SyntheticSum() { return 0; }\n')
        self.finish()

    def test_final_failure_removes_worktrees_and_branches_keeps_near_misses(self):
        self.claim()
        self.finish(passed=False)
        self.claim('fallback')
        wq.finish(self.q, self.unit['dir'], ['{"rva":"0x1000","result":"fail"}',
                                            '{"rva":"0x1010","result":"fail"}'], tier='fallback')
        unit = self.claim('strong')
        near = self.directory / 'near-miss/0x1000.cpp'
        near.parent.mkdir()
        near.write_text('// synthetic near miss\n')
        wq.finish(self.q, self.unit['dir'], ['{"rva":"0x1000","result":"fail"}',
                                            '{"rva":"0x1010","result":"fail"}'], tier='strong')
        self.assertFalse(Path(unit['draft']['tree']).exists())
        self.assertEqual(git(self.root, 'branch', '--list', 'draft/*'), '')
        self.assertTrue(near.is_file())
        with self.assertRaisesRegex(ValueError, 'no live checkout'):
            drafts.route_attempt(self.directory, self.root)
        with self.assertRaisesRegex(ValueError, 'clean harvested snapshot'):
            drafts.harvest_for_confirmation(self.directory)

    def test_final_failure_after_prior_pass_preserves_harvest_but_removes_draft_branches(self):
        self.claim()
        self.finish()
        for tier in ('fallback', 'strong'):
            self.claim(tier)
            self.real_run = subprocess.run
            with patch('draft_worktrees.subprocess.run', side_effect=self.clean_attempt):
                wq.finish(self.q, self.unit['dir'], ['{"rva":"0x1010","result":"fail"}'], tier=tier)
        harvest = drafts.current(self.root, self.unit)
        self.assertFalse(Path(harvest['tree']).exists())
        self.assertEqual(git(self.root, 'branch', '--list', 'draft/*'), '')
        self.assertEqual(git(self.root, 'rev-parse', 'refs/harvests/g-foo/strong'), harvest['commit'])
        self.assertTrue((Path(harvest['attempt']) / 'candidate.obj').is_file())

    def test_integration_and_state_use_harvest_even_after_working_trees_change(self):
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('int harvested;\n')
        self.finish()
        harvest = drafts.current(self.root, self.unit)
        rec_path = self.root / f'reports/{BUILD}/0x1000.json'
        rec = drafts.read(rec_path)
        rec['source']['digest'] = harvest['digest']
        rec['source']['translation_unit'] = harvest['sources']
        drafts.save(rec_path, rec)
        (tree / self.unit['sources'][-1]).write_text('int dirty_draft;\n')
        (self.root / self.unit['sources'][-1]).write_text('int dirty_shared;\n')
        fn = flow.inventory(self.root)['functions'][0]
        self.assertEqual(flow.record_state(self.root, fn), 'confirmed')
        made = flow.review_group(self.root, self.repo.fdir, select={fn['id']})
        group = flow.load_group(self.repo.fdir, made[0])
        frozen = Path(group['review_root'])
        self.assertEqual((frozen / self.unit['sources'][-1]).read_text(), 'int harvested;\n')
        brief = self.root / group['brief']
        self.assertIn(str(frozen), brief.read_text())
        rerun = self.root / '.local/briefs' / f'rerun-{group["name"]}.md'
        self.assertIn(harvest['task'], rerun.read_text())
        dest = self.tmp / 'integration'
        git(self.root, 'worktree', 'add', '--detach', str(dest), 'origin/main')
        flow.carry_into_tree(self.root, dest, ['0x1000'], {'0x1000': fn})
        self.assertEqual((dest / self.unit['sources'][-1]).read_text(), 'int harvested;\n')
        # Integration cleanup requires accepted origin state and exactly the harvested digest.
        data = flow.inventory(dest)
        data['functions'][0]['status'] = 'matched'
        drafts.save(dest / 'data/progress.json', data)
        git(dest, 'add', 'data/progress.json', *self.unit['sources'])
        git(dest, 'commit', '-m', 'synthetic integration')
        git(dest, 'push', 'origin', 'HEAD:main')
        active = self.q / 'claims-fallback/g-foo.lock'
        active.parent.mkdir()
        wq.try_create(active, 'next-tier', wq.now(), 'claude-low', 'fallback')
        drafts.cleanup_integrated(self.root)
        self.assertTrue(tree.exists())
        active.unlink()
        drafts.cleanup_integrated(self.root)
        self.assertFalse(tree.exists())
        self.assertTrue(drafts.current(self.root, self.unit)['integrated'])

    def test_confirm_reads_commit_and_not_mutable_draft(self):
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('int harvested;\n')
        self.finish()
        (tree / self.unit['sources'][-1]).write_text('int dirty_draft;\n')
        self.real_run = subprocess.run
        seen = []

        def run(command, cwd=None, **kwargs):
            if len(command) > 1 and ('verifier/bind.py' in str(command[1]) or 'verifier/confirm' in str(command[1])):
                seen.append((Path(cwd) / self.unit['sources'][-1]).read_text())
                return subprocess.CompletedProcess(command, 0)
            return self.real_run(command, cwd=cwd, **kwargs)

        with patch('draft_worktrees.subprocess.run', side_effect=run):
            self.assertEqual(drafts.confirm_one(self.root, self.directory, ['--out', str(self.tmp / 'out')]), 0)
        self.assertEqual(seen, ['int harvested;\n', 'int harvested;\n'])


if __name__ == '__main__':
    unittest.main()
