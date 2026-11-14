"""Pipelined publication and tooling batching on tiny synthetic git repositories."""
import json
from pathlib import Path
import socket
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_flow_operations import Operations as _Fixture
from test_flow import flow, git
import flow_lane as lane
import flow_tooling as tooling

setup, make_commit = _Fixture.setUp, _Fixture.tooling_commit
enqueue_groups = _Fixture.enqueue
del _Fixture


class Throughput(unittest.TestCase):
    setUp = setup
    tooling_commit = make_commit
    enqueue = enqueue_groups

    def other(self, name, filename, content):
        root = self.tmp / name
        git(self.root, 'clone', '--quiet', '--branch', 'main', str(self.repo.origin), str(root))
        git(root, 'config', 'user.name', 'Synthetic')
        git(root, 'config', 'user.email', 'synthetic@example.invalid')
        (root / filename).write_text(content)
        with (root / '.gitignore').open('a') as stream:
            stream.write('__pycache__/\n')
        git(root, 'add', filename, '.gitignore')
        git(root, 'commit', '--quiet', '-m', 'synthetic tooling ' + name)
        return root

    def test_waiting_input_clone_uses_main_when_bare_head_is_unborn(self):
        git(self.repo.origin, 'symbolic-ref', 'HEAD', 'refs/heads/unborn')
        other = self.other('unborn-default', 'other.txt', 'synthetic input\n')
        self.assertEqual(git(other, 'merge-base', 'HEAD', 'origin/main'),
                         git(self.repo.origin, 'rev-parse', 'main'))

    def test_next_checks_overlap_ci_but_next_push_requires_previous_green(self):
        self.tooling_commit()
        a = git(self.root, 'rev-parse', 'HEAD')
        other = self.other('other', 'other-tool.txt', 'original synthetic tooling\n')
        waiting, checked, green = threading.Event(), threading.Event(), threading.Event()
        errors, results = [], []
        original_run, original_checks = lane.subprocess.run, flow.pre_push_checks
        def command(argv, *args, **kwargs):
            if 'tools/ci_status.py' in argv:
                sha = argv[argv.index('--commit') + 1]
                if sha == a:
                    waiting.set()
                    if not green.wait(10): raise RuntimeError('synthetic CI timeout')
                return SimpleNamespace(returncode=0, stdout='GREEN', stderr='')
            return original_run(argv, *args, **kwargs)
        def checks(root, *args, **kwargs):
            original_checks(root, *args, **kwargs)
            if Path(root) == other: checked.set()
        def publish(root):
            try: results.append(lane.publish_tooling(root, self.fdir, python=sys.executable, ci_wait=0))
            except BaseException as e: errors.append(e)
        with patch.object(lane.subprocess, 'run', side_effect=command), patch.object(flow, 'pre_push_checks', side_effect=checks):
            first = threading.Thread(target=publish, args=(self.root,)); first.start()
            try:
                self.assertTrue(waiting.wait(10))
                self.assertFalse(lane.running(self.fdir), 'CI waiter must release its build lease')
                second = threading.Thread(target=publish, args=(other,)); second.start()
                self.assertTrue(checked.wait(10), 'next full checks must overlap pending CI')
                self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), a, 'next tree pushed before GREEN')
            finally:
                green.set(); first.join(15)
                if 'second' in locals(): second.join(15)
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['state'] == 'done' and r.get('lane_hold_seconds') is not None for r in results))

    def test_red_predecessor_aborts_after_speculative_checks_without_push(self):
        self.tooling_commit()
        a = git(self.root, 'rev-parse', 'HEAD')
        base = git(self.repo.origin, 'rev-parse', 'main')
        other = self.other('other', 'other.txt', 'synthetic\n')
        original = lane.subprocess.run
        state = {'red': False}
        def command(argv, *args, **kwargs):
            if 'tools/ci_status.py' in argv:
                sha = argv[argv.index('--commit') + 1]
                code = 0 if sha == base else 1 if state['red'] else 2
                return SimpleNamespace(returncode=code, stdout='synthetic CI', stderr='')
            return original(argv, *args, **kwargs)
        with patch.object(lane.subprocess, 'run', side_effect=command):
            with self.assertRaisesRegex(flow.FlowError, 'tooling CI pending'):
                lane.publish_tooling(self.root, self.fdir, python=sys.executable, ci_wait=0)
            state['red'] = True
            with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
                with self.assertRaisesRegex(flow.FlowError, 'origin CI is not green'):
                    lane.publish_tooling(other, self.fdir, python=sys.executable, ci_wait=0)
                checks.assert_called_once()
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), a)

    def test_live_foreign_receipt_waits_and_stale_receipt_names_correct_resume(self):
        receipt = dict(id='foreign', root=str(self.tmp / 'foreign'), branch='main', kind='tooling',
                       state='running', integrated=None, owner=lane.process_owner())
        path = self.fdir / 'lane/tooling/foreign.json'; lane.write(path, receipt)
        done, errors = threading.Event(), []
        def waiter():
            try: lane.wait_for_owner(self.root, self.fdir, 'tooling', None, True); done.set()
            except BaseException as e: errors.append(e)
        thread = threading.Thread(target=waiter); thread.start()
        try:
            self.assertFalse(done.wait(0.15))
            with lane.state_lock(self.fdir):
                receipt['state'] = 'done'; lane.write(path, receipt)
            self.assertTrue(done.wait(2))
        finally: thread.join(3)
        self.assertEqual(errors, [])
        receipt.update(state='running', owner=dict(pid=999999999, host=socket.gethostname(), birth='dead'))
        lane.write(path, receipt)
        lane.wait_for_owner(self.root, self.fdir, 'tooling', None, True)
        with lane.lane_lock(self.fdir):
            lane.recover_stale(self.fdir)
        recovered = lane.read(path)
        self.assertEqual(recovered['state'], 'stale')
        self.assertIn('--resume foreign', lane.run_status(self.root, self.fdir, recovered)['resume_command'])
        self.assertTrue(flow.parser().parse_args(['lane-run', '--wait-lane']).wait_lane)
        self.assertTrue(flow.parser().parse_args(['lane-run']).wait_lane)

    def test_tooling_batches_once_and_drops_only_merge_conflict(self):
        self.tooling_commit()
        first = tooling.enqueue(self.root, self.fdir, 'main')
        other = self.other('second', 'second.txt', 'second synthetic input\n')
        second = tooling.enqueue(other, self.fdir, 'main')
        conflict = self.other('conflict', 'tooling.txt', 'conflicting synthetic input\n')
        third = tooling.enqueue(conflict, self.fdir, 'main')
        before = git(self.root, 'rev-parse', 'HEAD')
        with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        checks.assert_called_once()
        self.assertEqual(result['state'], 'done')
        states = {i['id']: lane.read(self.fdir / 'lane/tooling-queue' / (i['id'] + '.json'))['state'] for i in (first, second, third)}
        self.assertEqual(states[second['id']], 'done')
        self.assertEqual(sorted(states.values()), ['done', 'done', 'dropped'])
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), before, 'input checkout must not change')
        tree = Path(result['tree'])
        self.assertEqual((tree / 'second.txt').read_text(), 'second synthetic input\n')
        self.assertTrue(result['tooling_dropped'][0]['reason'])

    def test_combined_check_isolates_only_bad_tooling_input(self):
        self.tooling_commit()
        a = tooling.enqueue(self.root, self.fdir, 'main')
        bad = self.other('bad', 'bad.txt', 'synthetic failing input\n')
        b = tooling.enqueue(bad, self.fdir, 'main')
        good = self.other('good', 'good.txt', 'synthetic good input\n')
        c = tooling.enqueue(good, self.fdir, 'main')
        original = flow.pre_push_checks
        def checks(root, *args, **kwargs):
            if (Path(root) / 'bad.txt').exists(): raise flow.FlowError('synthetic check failure')
            return original(root, *args, **kwargs)
        with patch.object(flow, 'pre_push_checks', side_effect=checks):
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        states = {i['id']: lane.read(self.fdir / 'lane/tooling-queue' / (i['id'] + '.json'))['state'] for i in (a, b, c)}
        self.assertEqual(states, {a['id']: 'done', b['id']: 'dropped', c['id']: 'done'})
        self.assertFalse((Path(result['tree']) / 'bad.txt').exists())
        self.assertTrue((Path(result['tree']) / 'good.txt').is_file())
        self.assertIn('synthetic check failure', result['tooling_dropped'][0]['reason'])

    def test_gate_tooling_defers_function_queue_but_plain_tooling_mixes(self):
        item = dict(paths=['tools/check.py'])
        self.assertFalse(tooling.mixed_safe([item]))
        self.assertTrue(tooling.mixed_safe([dict(paths=['docs/example.md', 'tools/example_generator.py'])]))

    def test_safe_tooling_and_reviewed_groups_share_one_checked_push(self):
        self.tooling_commit()
        tooling.enqueue(self.root, self.fdir, 'main')
        self.enqueue()
        with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        checks.assert_called_once()
        self.assertEqual(result['integrated']['accepted'], 3)
        self.assertTrue((Path(result['tree']) / 'tooling.txt').is_file())
        self.assertTrue(all(i['state'] == 'done' for i in result['items']))

    def test_whole_tree_baseline_failure_never_blames_a_tooling_input(self):
        self.tooling_commit()
        item = tooling.enqueue(self.root, self.fdir, 'main')
        before = git(self.repo.origin, 'rev-parse', 'main')
        with patch.object(flow, 'pre_push_checks', side_effect=flow.FlowError('synthetic whole tree failure')):
            with self.assertRaisesRegex(flow.FlowError, 'whole-tree baseline check failed'):
                lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), before)
        self.assertEqual(lane.read(self.fdir / 'lane/tooling-queue' / (item['id'] + '.json'))['state'], 'running')

    def test_rebase_conflict_is_terminal_and_does_not_block_next_input(self):
        self.tooling_commit()
        original_head = git(self.root, 'rev-parse', 'HEAD')
        other = self.other('moving', 'moving.txt', 'synthetic moving origin\n')
        git(other, 'push', '--quiet', 'origin', 'HEAD:main')
        original = flow.git
        def command(root, *args, **kwargs):
            if args[0] == 'rebase': raise flow.FlowError('git rebase origin/main failed: synthetic conflict')
            return original(root, *args, **kwargs)
        with patch.object(flow, 'git', side_effect=command), self.assertRaisesRegex(flow.FlowError, 'rebase'):
            lane.publish_tooling(self.root, self.fdir, python=sys.executable, ci_wait=0)
        failed = lane.read(next((self.fdir / 'lane/tooling').glob('*.json')))
        self.assertEqual(failed['state'], 'conflict')
        self.assertIn('--resume', failed['resume_command'])
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), original_head)
        (other / 'second.txt').write_text('synthetic second\n')
        git(other, 'add', 'second.txt'); git(other, 'commit', '--quiet', '-m', 'next tooling input')
        result = lane.publish_tooling(other, self.fdir, python=sys.executable, ci_wait=0)
        self.assertEqual(result['state'], 'done')
        self.assertEqual(lane.read(self.fdir / 'lane/tooling' / (failed['id'] + '.json'))['state'], 'conflict')

    def test_pushed_function_ci_resume_does_not_wait_for_another_build_lock(self):
        self.enqueue()
        before = git(self.repo.origin, 'rev-parse', 'main')
        original = lane.subprocess.run
        def pending(argv, *args, **kwargs):
            if 'tools/ci_status.py' in argv:
                sha = argv[argv.index('--commit') + 1]
                return SimpleNamespace(returncode=0 if sha == before else 2, stdout='synthetic CI', stderr='')
            return original(argv, *args, **kwargs)
        with patch.object(lane.subprocess, 'run', side_effect=pending), self.assertRaises(flow.FlowError):
            lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        receipt = lane.read(next((self.fdir / 'lane/runs').glob('*.json')))
        with lane.lane_lock(self.fdir), patch.object(flow, 'pre_push_checks', side_effect=AssertionError('must not repeat checks')):
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0, resume=receipt['id'])
        self.assertEqual(result['state'], 'done')

    def test_python_314_frontend_selects_313_and_refuses_broken_override(self):
        with patch.object(lane.sys, 'version_info', (3, 14)), patch.object(lane.shutil, 'which', return_value='/synthetic/python3.13'), \
                patch.object(lane.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as call:
            self.assertEqual(lane.lane_python('/synthetic/python3.14'), '/synthetic/python3.13')
            self.assertIn('pyexpat', call.call_args.args[0][-1])
        with patch.dict(lane.os.environ, SKYRIM_LANE_PYTHON='/synthetic/python3.14'), \
                patch.object(lane.subprocess, 'run', return_value=SimpleNamespace(returncode=1)):
            with self.assertRaisesRegex(flow.FlowError, 'python3.13 with working pyexpat'):
                lane.lane_python('/synthetic/python3.14')

    def test_cli_waits_for_busy_lane_then_completes(self):
        import subprocess
        import time
        with lane.lane_lock(self.fdir):
            proc = subprocess.Popen([sys.executable, str(flow.TOOLS / 'flow.py'), '--root', str(self.root),
                                     '--flow-dir', str(self.fdir), 'lane-run', '--wait-lane', '--min-free-gb', '0'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(0.15)
            self.assertIsNone(proc.poll())
        out, err = proc.communicate(timeout=10)
        self.assertEqual(proc.returncode, 0, out + err)
        self.assertIn('empty', out)

    def test_dead_local_owner_is_skipped_without_touching_inputs_or_live_receipts(self):
        root = self.tmp / 'preserved-input'; root.mkdir(); (root / 'evidence.txt').write_text('preserve this\n')
        dead = dict(id='dead', root=str(root), branch='main', state='running', integrated=None, kind='tooling',
                    owner=dict(pid=999999999, host=socket.gethostname(), birth='dead'))
        live = dict(dead, id='live', owner=lane.process_owner())
        foreign = dict(dead, id='foreign-host', owner=dict(pid=999999999, host='different-host', birth='unknown'))
        for r in (dead, live, foreign): lane.write(self.fdir / 'lane/tooling' / (r['id'] + '.json'), r)
        before = (self.fdir / 'lane/tooling/live.json').read_bytes()
        with lane.lane_lock(self.fdir): lane.recover_stale(self.fdir)
        self.assertEqual(lane.read(self.fdir / 'lane/tooling/dead.json')['state'], 'stale')
        self.assertEqual((root / 'evidence.txt').read_text(), 'preserve this\n')
        self.assertEqual((self.fdir / 'lane/tooling/live.json').read_bytes(), before)
        self.assertEqual(lane.read(self.fdir / 'lane/tooling/foreign-host.json')['state'], 'running')

    def test_repeated_tooling_frontend_returns_batch_receipt_without_rechecking(self):
        self.tooling_commit()
        item = tooling.enqueue(self.root, self.fdir, 'main')
        result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        with patch.object(flow, 'pre_push_checks', side_effect=AssertionError('must not recheck')):
            again = lane.publish_tooling(self.root, self.fdir, python=sys.executable, ci_wait=0, wait_lane=True)
        self.assertEqual(result['id'], again['id'])
        self.assertEqual(tooling.enqueue(self.root, self.fdir, 'main')['id'], item['id'])

    def test_ci_observers_share_one_exact_sha_watch(self):
        self.tooling_commit()
        item = tooling.enqueue(self.root, self.fdir, 'main')
        before = git(self.repo.origin, 'rev-parse', 'main')
        original = lane.subprocess.run
        def pending(argv, *args, **kwargs):
            if 'tools/ci_status.py' in argv:
                sha = argv[argv.index('--commit') + 1]
                return SimpleNamespace(returncode=0 if sha == before else 2, stdout='synthetic CI', stderr='')
            return original(argv, *args, **kwargs)
        with patch.object(lane.subprocess, 'run', side_effect=pending), self.assertRaises(flow.FlowError):
            lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        receipt = lane.read(next((self.fdir / 'lane/runs').glob('*.json')))
        entered, release = threading.Event(), threading.Event()
        calls, results, errors = [], [], []
        def green(argv, *args, **kwargs):
            if 'tools/ci_status.py' in argv:
                calls.append(argv); entered.set()
                if not release.wait(5): raise RuntimeError('synthetic CI timeout')
                return SimpleNamespace(returncode=0, stdout='GREEN', stderr='')
            return original(argv, *args, **kwargs)
        def observe():
            try: results.append(lane.finish_run(self.root, self.fdir, receipt, sys.executable, 0))
            except BaseException as error: errors.append(error)
        with patch.object(lane.subprocess, 'run', side_effect=green):
            a = threading.Thread(target=observe); a.start()
            try:
                self.assertTrue(entered.wait(5))
                b = threading.Thread(target=observe); b.start()
            finally:
                release.set(); a.join(10)
                if 'b' in locals(): b.join(10)
        self.assertEqual(errors, [])
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['state'] == 'done' for r in results))
        with patch.object(flow, 'pre_push_checks', side_effect=AssertionError('must not repeat checks')):
            resumed = lane.publish_tooling(self.root, self.fdir, python=sys.executable, ci_wait=0, resume=receipt['id'])
        self.assertEqual(resumed['id'], receipt['id'])
        self.assertFalse((self.fdir / 'lane/tooling' / (receipt['id'] + '.json')).exists())
