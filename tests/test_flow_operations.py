"""Operational lane rules, using only tiny synthetic repositories."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_flow_lane import PushLane as _Fixture
from test_flow import flow, git, FUNCS
import flow_lane as lane
import flow_cleanup
import resource_admission as disk
import lint_review_readiness as readiness

setup_fixture, enqueue_fixture, run_fixture = _Fixture.setUp, _Fixture.enqueue, _Fixture.lane
del _Fixture


class Operations(unittest.TestCase):
    setUp = setup_fixture
    enqueue = enqueue_fixture
    lane = run_fixture

    def tooling_commit(self, ci=None):
        if ci:
            (self.root / 'tools/ci_status.py').write_text(ci)
        (self.root / 'tooling.txt').write_text('original tooling fixture\n')
        with (self.root / '.gitignore').open('a') as stream:
            stream.write('__pycache__/\n')
        git(self.root, 'add', 'tooling.txt', 'tools/ci_status.py', '.gitignore')
        git(self.root, 'commit', '--quiet', '-m', 'tooling fixture')

    def test_tooling_push_takes_lane_and_leaves_state_free_during_checks(self):
        self.tooling_commit()
        with lane.lane_lock(self.fdir), self.assertRaisesRegex(flow.FlowError, 'already running'):
            lane.publish_tooling(self.root, self.fdir)
        original = flow.pre_push_checks
        def checks(root, commit, python, **kwargs):
            self.assertTrue(lane.running(self.fdir))
            import subprocess
            group = flow.load_group(self.fdir, self.names[0])
            compare = self.tmp / 'rerun.txt'
            compare.write_text(''.join(r + ' AGREE\n' for r in group['sampled']))
            result = subprocess.run([sys.executable, str(flow.TOOLS / 'flow.py'), '--root', str(self.root),
                                     '--flow-dir', str(self.fdir), 'record-rerun', group['name'],
                                     '--compare', str(compare)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            original(root, commit, python, **kwargs)
        with patch.object(flow, 'pre_push_checks', side_effect=checks) as checked:
            result = lane.publish_tooling(self.root, self.fdir, ci_wait=0, python=sys.executable)
        self.assertEqual(checked.call_count, 1)
        self.assertEqual(result['state'], 'done')
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), result['integrated']['commit'])
        self.assertFalse(lane.running(self.fdir))

    def test_tooling_cli_defaults_to_the_common_shared_flow_directory(self):
        other = self.tmp / 'tooling-worktree'
        git(self.root, 'worktree', 'add', '--quiet', '--detach', str(other), 'HEAD')
        with patch.object(lane, 'publish_tooling', return_value={}) as publish, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(flow.main(['--root', str(other), 'tooling-push']), 0)
        self.assertEqual(publish.call_args.args[1].resolve(), self.fdir.resolve())

    def test_tooling_pending_ci_resumes_without_checks_or_another_push(self):
        base = git(self.root, 'rev-parse', 'HEAD')
        self.tooling_commit("from pathlib import Path\nimport sys\nsha=sys.argv[sys.argv.index('--commit')+1]\nsys.exit(0 if sha==" + repr(base) + " or Path('.local/ci-ok').exists() else 2)\n")
        with self.assertRaisesRegex(flow.FlowError, 'tooling CI pending'):
            lane.publish_tooling(self.root, self.fdir, ci_wait=0, python=sys.executable)
        receipt = lane.read(next((self.fdir / 'lane/tooling').glob('*.json')))
        (self.root / '.local/ci-ok').write_text('ready')
        with patch.object(flow, 'pre_push_checks', side_effect=AssertionError('duplicate checks')):
            result = lane.publish_tooling(self.root, self.fdir, ci_wait=0, python=sys.executable, resume=receipt['id'])
        self.assertEqual(result['integrated']['commit'], receipt['integrated']['commit'])
        self.assertEqual(result['integrated']['pushed'], receipt['integrated']['pushed'])

    def test_dead_run_is_reported_and_retirement_is_only_explicit(self):
        self.enqueue()
        receipt = self.lane(push=False)
        receipt['owner'] = dict(pid=999999999, host=socket.gethostname(), birth='dead')
        lane.save_run(self.fdir, receipt)
        path = self.fdir / 'lane/runs' / (receipt['id'] + '.json')
        before = path.read_bytes()
        status = lane.run_status(self.root, self.fdir, receipt)
        self.assertEqual(status['status'], 'stale')
        self.assertIn('--resume ' + receipt['id'], status['resume_command'])
        self.assertIn('lane-retire ' + receipt['id'], status['retire_command'])
        actions = flow.next_actions(self.root, self.fdir, online=False)
        self.assertTrue(any('--resume ' + receipt['id'] in text for _, text in actions))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(flow.main(['--root', str(self.root), '--flow-dir', str(self.fdir),
                                        '--offline', 'next-actions']), 0)
        self.assertIn('--flow-dir ' + str(self.fdir), output.getvalue())
        self.assertEqual(before, path.read_bytes())
        retired = lane.retire(self.root, self.fdir, receipt['id'], 'synthetic replacement')
        self.assertEqual(retired['state'], 'retired')
        self.assertTrue(Path(retired['tree']).exists())
        self.assertEqual(self.enqueue()[0]['state'], 'queued')

    def test_checked_unpushed_tooling_resumes_without_duplicate_checks(self):
        self.tooling_commit("from pathlib import Path\nimport sys\nsys.exit(0 if Path('.local/ci-ok').exists() else 2)\n")
        before = git(self.repo.origin, 'rev-parse', 'main')
        with self.assertRaisesRegex(flow.FlowError, 'origin CI is not green'):
            lane.publish_tooling(self.root, self.fdir, ci_wait=0, python=sys.executable)
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), before)
        receipt = lane.read(next((self.fdir / 'lane/tooling').glob('*.json')))
        (self.root / '.local/ci-ok').write_text('green')
        with patch.object(flow, 'pre_push_checks', side_effect=AssertionError('duplicate checks')):
            result = lane.publish_tooling(self.root, self.fdir, ci_wait=0, python=sys.executable, resume=receipt['id'])
        self.assertEqual(result['integrated']['commit'], receipt['integrated']['commit'])

    def test_tooling_recovers_server_push_before_checkpoint_without_repushing(self):
        self.tooling_commit("from pathlib import Path\nimport sys\nsys.exit(0 if Path('.local/ci-ok').exists() else 2)\n")
        with self.assertRaisesRegex(flow.FlowError, 'origin CI is not green'):
            lane.publish_tooling(self.root, self.fdir, ci_wait=0, python=sys.executable)
        receipt = lane.read(next((self.fdir / 'lane/tooling').glob('*.json')))
        git(self.root, 'push', '--quiet', 'origin', 'HEAD:main')
        (self.root / '.local/ci-ok').write_text('green')
        original = lane.subprocess.run
        with patch.object(flow, 'pre_push_checks', side_effect=AssertionError('duplicate checks')), \
                patch.object(lane.subprocess, 'run', wraps=original) as commands:
            result = lane.publish_tooling(self.root, self.fdir, ci_wait=0, python=sys.executable, resume=receipt['id'])
        self.assertEqual(result['state'], 'done')
        self.assertFalse(any(call.args[0][:2] == ['git', 'push'] for call in commands.call_args_list))

    def test_escalations_are_grouped_by_action_and_category_with_counts(self):
        group = max((flow.load_group(self.fdir, name) for name in self.names), key=lambda g: len(g['functions']))
        self.repo.save_review(group['task_id'], [(r, size, self.repo.digest(r), 'escalate', 'systemic')
                                               for r, size, _ in FUNCS if hex(r) in group['functions']])
        stops = [text for kind, text in flow.next_actions(self.root, self.fdir, online=False)
                 if kind == 'stop' and group['name'] in text and 'systemic' in text]
        self.assertEqual(len(stops), 1)
        self.assertIn(str(len(group['functions'])) + ' functions', stops[0])

    def test_tooling_lost_race_rebases_and_checks_the_final_tree(self):
        self.tooling_commit()
        checked = []
        original = flow.pre_push_checks
        def advance(root, commit, python, **kwargs):
            original(root, commit, python, **kwargs)
            checked.append(commit)
            if len(checked) == 1:
                other = self.tmp / 'publisher'
                git(self.root, 'clone', '--quiet', '--branch', 'main', str(self.repo.origin), str(other))
                git(other, 'config', 'user.name', 'test')
                git(other, 'config', 'user.email', 'test@example.invalid')
                (other / 'incoming.txt').write_text('original fixture\n')
                git(other, 'add', 'incoming.txt')
                git(other, 'commit', '--quiet', '-m', 'incoming')
                git(other, 'push', '--quiet', 'origin', 'main')
        with patch.object(flow, 'pre_push_checks', side_effect=advance):
            result = lane.publish_tooling(self.root, self.fdir, ci_wait=0, python=sys.executable)
        self.assertEqual(len(checked), 2)
        self.assertEqual(result['integrated']['commit'], checked[-1])
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), checked[-1])

    def test_pid_reuse_is_not_a_live_owner_and_pushed_run_cannot_retire(self):
        owner = lane.process_owner()
        self.assertTrue(lane.owner_alive(owner))
        self.assertFalse(lane.owner_alive(dict(owner, birth='different process')))
        self.enqueue()
        receipt = self.lane()
        receipt['state'] = 'running'
        lane.save_run(self.fdir, receipt)
        with self.assertRaisesRegex(flow.FlowError, 'pushed run must resume CI'):
            lane.retire(self.root, self.fdir, receipt['id'], 'must refuse')

    def test_legacy_dead_run_is_stale_even_while_another_tooling_job_owns_lane(self):
        self.enqueue()
        receipt = self.lane(push=False)
        receipt.pop('owner')
        with lane.lane_lock(self.fdir, purpose='tooling'):
            self.assertEqual(lane.run_status(self.root, self.fdir, receipt, active=True)['status'], 'stale')
        with lane.lane_lock(self.fdir, purpose='integration'):
            self.assertEqual(lane.run_status(self.root, self.fdir, receipt, active=True)['status'], 'running')

    def test_green_clone_cleanup_keeps_json_logs_refs_stashes_and_receipt(self):
        self.enqueue()
        receipt = self.lane()
        tree = Path(receipt['tree'])
        (tree / '.local/keep.json').write_text('{"evidence": true}\n')
        (tree / '.local/keep.log').write_text('synthetic log\n')
        (tree / 'reconstruction/x/Foo.cpp').write_text('int changed;\n')
        git(tree, 'stash', 'push', '--quiet')
        shutil.rmtree(tree / 'tests/__pycache__')  # disposable bytecode from this tiny fixture
        refs = git(tree, 'show-ref')
        stashes = git(tree, 'stash', 'list')
        record_path = self.fdir / 'lane/runs' / (receipt['id'] + '.json')
        record = record_path.read_bytes()
        preview = flow_cleanup.cleanup(self.root, self.fdir, dry_run=True)
        self.assertTrue(preview[0].get('would_remove'), preview)
        self.assertTrue((tree / 'data/progress.json').exists())
        results = flow_cleanup.cleanup(self.root, self.fdir)
        self.assertTrue(results[0]['removed'], results)
        archive = Path(results[0]['archive'])
        self.assertEqual((archive / 'files/.local/keep.log').read_text(), 'synthetic log\n')
        self.assertTrue((archive / 'files/.local/keep.json').is_file())
        self.assertTrue((tree / '.git').is_dir())
        self.assertFalse((tree / 'data').exists())
        self.assertEqual(git(tree, 'show-ref'), refs)
        self.assertEqual(git(tree, 'stash', 'list'), stashes)
        self.assertEqual(record_path.read_bytes(), record)

    def test_cleanup_refuses_dirty_tree_and_removes_clean_agree_rerun(self):
        group = flow.load_group(self.fdir, self.names[0])
        tree = self.fdir / 'rerun' / group['name'] / 'tree'
        tree.parent.mkdir(parents=True, exist_ok=True)
        git(self.root, 'worktree', 'add', '--quiet', '--detach', str(tree), 'HEAD')
        flow.drafts.label(tree, 'synthetic owner', group['name'], 'rerun')
        (tree / 'reconstruction/x/Foo.cpp').write_text('int changed;\n')
        refused = flow_cleanup.cleanup(self.root, self.fdir)
        self.assertIn('dirty checkout', refused[0]['reason'])
        git(tree, 'restore', 'reconstruction/x/Foo.cpp')
        result = flow_cleanup.cleanup(self.root, self.fdir)
        self.assertTrue(result[0]['removed'], result)
        self.assertFalse(tree.exists())

    def test_cleanup_harvest_keeps_branch_and_harvest_and_skips_active_claim(self):
        queue = self.root / '.local/queue/small'
        queue.mkdir(parents=True, exist_ok=True)
        unit_dir = '.local/tasks/g/unit-a'
        (queue / 'queue.tsv').write_text(unit_dir + '\treconstruction/x/Foo.cpp\t0x1000\t3\n')
        tree = self.root / '.local/worktrees/draft/unit-a-first'
        tree.parent.mkdir(parents=True)
        git(self.root, 'worktree', 'add', '--quiet', '-b', 'draft/unit-a-first', str(tree), 'HEAD')
        flow.drafts.label(tree, 'synthetic owner', 'unit-a', 'draft')
        head = git(tree, 'rev-parse', 'HEAD')
        git(self.root, 'update-ref', 'refs/harvests/unit-a/first', head)
        harvest = self.root / unit_dir / 'harvest.json'
        lane.write(harvest, dict(commit=head, tree=str(tree), tier='first'))
        before = harvest.read_bytes()
        claim = queue / 'claims/unit-a.lock'
        lane.write(claim, dict(worker='synthetic'))
        self.assertEqual(flow_cleanup.cleanup(self.root, self.fdir), [])
        claim.unlink()
        result = flow_cleanup.cleanup(self.root, self.fdir)
        self.assertTrue(result[0]['removed'], result)
        self.assertFalse(tree.exists())
        self.assertEqual(git(self.root, 'rev-parse', 'draft/unit-a-first'), head)
        self.assertEqual(harvest.read_bytes(), before)


class AdmissionAndReadiness(unittest.TestCase):
    def test_soft_floor_requires_explicit_override_and_hard_floor_never_does(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            with patch.object(disk.shutil, 'disk_usage', return_value=SimpleNamespace(free=5_000_000_000)):
                with self.assertRaisesRegex(ValueError, 'soft floor 10'):
                    disk.admit(directory, 'synthetic confirm')
                disk.admit(directory, 'synthetic confirm', allow_low_disk=True)
                disk.admit(directory, 'synthetic confirm', soft_gb=4)
            with patch.object(disk.shutil, 'disk_usage', return_value=SimpleNamespace(free=2_999_000_000)):
                with self.assertRaisesRegex(ValueError, 'hard floor'):
                    disk.admit(directory, 'synthetic job', hard_gb=0, soft_gb=0, allow_low_disk=True)
            for setting in ('nan', 'inf', '-1', 'wrong'):
                with self.assertRaises(ValueError):
                    disk.threshold(setting, 'UNUSED', '10')

    def test_origin_statement_is_about_code_not_names_or_exposure(self):
        missing = '// Widget.\n// Source exposure: binary-analysis. Names origin: GUESS.\nint a;\n'
        self.assertTrue(readiness.origin_statement_problems('Widget.cpp', missing))
        for origin in ('// Origin: original reconstruction.\n', '// Original implementation.\n',
                       '// Provenance: adapted from an authorized source.\n'):
            self.assertEqual(readiness.origin_statement_problems('Widget.cpp', origin + missing), [])

    def test_truncated_mit_fragment_is_caught_without_weakening_old_lint(self):
        from test_lint_reconstruction import MIT_TEXT
        fragment = '// Copyright (c) Synthetic Author\n// permission is hereby\n'
        self.assertTrue(readiness.truncated_mit_problems('Widget.h', fragment))
        self.assertEqual(readiness.truncated_mit_problems('Widget.h', '// Origin: original work.\n'), [])
        complete = '\n'.join('// ' + line for line in MIT_TEXT.splitlines())
        self.assertEqual(readiness.truncated_mit_problems('Widget.h', complete), [])

    def test_confirm_admission_runs_before_any_verification_and_override_is_soft_only(self):
        import runpy
        confirm = runpy.run_path(str(flow.TOOLS / 'verifier/confirm'))['main']
        pipeline = confirm.__globals__['pipeline']
        error = io.StringIO()
        with patch.object(pipeline, 'resolve_task_dir', side_effect=pipeline.PipelineError('after admission')) as resolve:
            with patch.object(disk.shutil, 'disk_usage', return_value=SimpleNamespace(free=5_000_000_000)):
                with patch.object(sys, 'argv', ['confirm', 'synthetic']), contextlib.redirect_stderr(error):
                    self.assertEqual(confirm(), 2)
                resolve.assert_not_called()
                with patch.object(sys, 'argv', ['confirm', 'synthetic', '--allow-low-disk']), contextlib.redirect_stderr(error):
                    self.assertEqual(confirm(), 2)
                resolve.assert_called_once()
            resolve.reset_mock()
            with patch.object(disk.shutil, 'disk_usage', return_value=SimpleNamespace(free=2_000_000_000)), \
                    patch.object(sys, 'argv', ['confirm', 'synthetic', '--allow-low-disk']), contextlib.redirect_stderr(error):
                self.assertEqual(confirm(), 2)
            resolve.assert_not_called()
        self.assertIn('after admission', error.getvalue())
        self.assertIn('hard floor', error.getvalue())

    def test_harvest_confirm_propagates_soft_override_without_new_flags_to_old_tooling(self):
        import runpy
        confirm = runpy.run_path(str(flow.TOOLS / 'verifier/confirm'))['main']
        pipeline = confirm.__globals__['pipeline']
        with patch.object(disk.shutil, 'disk_usage', return_value=SimpleNamespace(free=5_000_000_000)), \
                patch.object(pipeline, 'resolve_task_dir', return_value=Path('/synthetic-task')), \
                patch.object(flow.drafts, 'harvest_for_confirmation', return_value={'commit': 'synthetic'}), \
                patch.object(flow.drafts, 'confirm_one', return_value=0) as child, \
                patch.object(sys, 'argv', ['confirm', 'synthetic', '--allow-low-disk']), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(confirm(), 0)
        self.assertEqual(child.call_args.kwargs['env']['SKYRIM_SOFT_FREE_GB'], '3')
        self.assertNotIn('--allow-low-disk', child.call_args.args[2])
