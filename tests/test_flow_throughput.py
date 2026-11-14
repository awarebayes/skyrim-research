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
            try: results.append(lane._publish_legacy_tooling(root, self.fdir, python=sys.executable, ci_wait=0))
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
                lane._publish_legacy_tooling(self.root, self.fdir, python=sys.executable, ci_wait=0)
            state['red'] = True
            with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
                with self.assertRaisesRegex(flow.FlowError, 'origin CI is not green'):
                    lane._publish_legacy_tooling(other, self.fdir, python=sys.executable, ci_wait=0)
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

    def test_lane_tooling_and_reviewed_groups_share_one_checked_push(self):
        other = self.other('lane-doc', 'tools/flow_tooling_example.py', '# synthetic tooling only\n')
        tooling.enqueue(other, self.fdir, 'main')
        self.enqueue()
        with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        checks.assert_called_once()
        self.assertEqual(result['integrated']['accepted'], 3)
        self.assertTrue(all(i['state'] == 'done' for i in result['items']))

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
            lane._publish_legacy_tooling(self.root, self.fdir, python=sys.executable, ci_wait=0)
        failed = lane.read(next((self.fdir / 'lane/tooling').glob('*.json')))
        self.assertEqual(failed['state'], 'conflict')
        self.assertIn('--resume', failed['resume_command'])
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), original_head)
        (other / 'second.txt').write_text('synthetic second\n')
        git(other, 'add', 'second.txt'); git(other, 'commit', '--quiet', '-m', 'next tooling input')
        result = lane._publish_legacy_tooling(other, self.fdir, python=sys.executable, ci_wait=0)
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

    def test_three_tooling_waiters_and_functions_get_one_push_and_own_receipts(self):
        roots = [self.other('batch-' + str(i), 'batch-' + str(i) + '.txt', 'synthetic\n')
                 for i in range(3)]
        items = [tooling.enqueue(root, self.fdir, 'main') for root in roots]
        heads = [git(root, 'rev-parse', 'HEAD') for root in roots]
        self.enqueue()
        ready = threading.Barrier(4)
        original_enqueue, original_run = tooling.enqueue, lane.subprocess.run
        results, errors, pushes, watches = [], [], [], []
        def enqueue(*args):
            item = original_enqueue(*args)
            ready.wait(timeout=10)
            return item
        def command(argv, *args, **kwargs):
            if argv[:2] == ['git', 'push']: pushes.append(argv)
            if 'tools/ci_status.py' in argv: watches.append(argv)
            return original_run(argv, *args, **kwargs)
        def publish(root):
            try:
                results.append(lane.publish_tooling(root, self.fdir, python=sys.executable,
                                                    ci_wait=0, wait_lane=True))
            except BaseException as error:
                errors.append(error)
        with patch.object(tooling, 'enqueue', side_effect=enqueue), \
                patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks, \
                patch.object(lane.subprocess, 'run', side_effect=command):
            with lane.lane_lock(self.fdir):
                workers = [threading.Thread(target=publish, args=(root,)) for root in roots]
                for worker in workers: worker.start()
                ready.wait(timeout=10)
                checks.assert_not_called()  # Waiters never validate their own checkouts.
            for worker in workers: worker.join(20)
        self.assertFalse(any(worker.is_alive() for worker in workers))
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 3)
        self.assertEqual(checks.call_count, 1)
        self.assertEqual(len(pushes), 1)
        self.assertEqual(len(watches), 2)  # predecessor gate + one exact pushed-SHA CI watch
        self.assertEqual(len({r['integrated']['commit'] for r in results}), 1)
        self.assertEqual({r['request']['id'] for r in results}, {i['id'] for i in items})
        for result in results:
            self.assertEqual(result['integrated']['accepted'], 3)
            self.assertEqual(result['request']['state'], 'done')
            self.assertEqual(result['request']['integrated']['ci'], 'green')
            self.assertNotIn(Path(checks.call_args.args[0]), roots)
        for item, root, head in zip(items, roots, heads):
            self.assertEqual(git(root, 'rev-parse', 'HEAD'), head)
            saved = lane.read(self.fdir / 'lane/tooling' / (item['id'] + '.json'))
            self.assertEqual(saved['integrated']['commit'], results[0]['integrated']['commit'])
            self.assertEqual(saved['kind'], 'tooling-request')
        self.assertTrue((self.fdir / 'events.jsonl').is_file())

    def test_conflicting_waiter_bounces_and_later_waiter_returns_pushed_sha(self):
        import contextlib
        import io
        first = self.other('first', 'same.txt', 'first input\n')
        conflict = self.other('conflicting', 'same.txt', 'conflicting input\n')
        last = self.other('last', 'last.txt', 'later input\n')
        items = [tooling.enqueue(root, self.fdir, 'main') for root in (first, conflict, last)]
        result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        with patch.object(flow, 'pre_push_checks', side_effect=AssertionError('waiter repeated checks')):
            with self.assertRaisesRegex(flow.FlowError, items[1]['revision'] + ' bounced:'):
                lane.publish_tooling(conflict, self.fdir, python=sys.executable, ci_wait=0, wait_lane=True)
            for root in (first, last):
                outcome = lane.publish_tooling(root, self.fdir, python=sys.executable, ci_wait=0, wait_lane=True)
                self.assertEqual(outcome['request']['state'], 'done')
                self.assertEqual(outcome['integrated']['commit'], result['integrated']['commit'])
        bounced = lane.read(self.fdir / 'lane/tooling' / (items[1]['id'] + '.json'))
        self.assertEqual(bounced['state'], 'dropped')
        self.assertIsNone(bounced['integrated'])
        self.assertIn('CONFLICT', bounced['reason'])
        self.assertTrue((Path(result['tree']) / 'last.txt').is_file())
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = flow.main(['--root', str(conflict), '--flow-dir', str(self.fdir),
                              'tooling-push', '--wait-lane'])
        self.assertEqual(code, 1)
        self.assertIn(items[1]['revision'] + ' bounced:', error.getvalue())

    def test_nonwaiting_frontend_registers_then_drains_every_queued_item(self):
        other = self.other('queued-first', 'queued.txt', 'queued first\n')
        first = tooling.enqueue(other, self.fdir, 'main')
        self.tooling_commit()
        self.enqueue()
        with lane.lane_lock(self.fdir), patch.object(flow, 'pre_push_checks') as checks:
            with self.assertRaisesRegex(flow.FlowError, 'already running'):
                lane.publish_tooling(self.root, self.fdir, python=sys.executable, ci_wait=0)
            checks.assert_not_called()
        with patch.object(flow, 'pre_push_checks', wraps=flow.pre_push_checks) as checks:
            result = lane.publish_tooling(self.root, self.fdir, python=sys.executable, ci_wait=0)
        checks.assert_called_once()
        self.assertEqual(result['integrated']['accepted'], 3)
        self.assertEqual([i['id'] for i in result['tooling']][0], first['id'])
        self.assertEqual(len(result['tooling_accepted']), 2)
        self.assertEqual(result['request']['state'], 'done')

    def test_origin_rebuild_does_not_retry_a_bounced_request(self):
        first = self.other('first-input', 'same.txt', 'first input\n')
        conflict = self.other('bounced-input', 'same.txt', 'conflicting input\n')
        tooling.enqueue(first, self.fdir, 'main')
        bounced = tooling.enqueue(conflict, self.fdir, 'main')
        checked = lane.run_lane(self.root, self.fdir, push=False, python=sys.executable, ci_wait=0)
        self.assertEqual(checked['tooling_dropped'][0]['item'], bounced['id'])
        winner = self.other('winner', 'advanced.txt', 'origin advanced\n')
        git(winner, 'push', '--quiet', 'origin', 'HEAD:main')
        with patch.object(flow, 'git', wraps=flow.git) as commands:
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0,
                                   resume=checked['id'])
        self.assertEqual(result['state'], 'done')
        self.assertFalse(any(c.args[1:4] == ('fetch', '--quiet', str(conflict))
                             for c in commands.call_args_list))
        self.assertEqual((Path(result['tree']) / 'same.txt').read_text(), 'first input\n')
        self.assertEqual(result['tooling_dropped'][0]['revision'], bounced['revision'])

    def test_bisection_has_logarithmic_depth_and_checks_final_survivors(self):
        roots = [self.other('split-' + str(i), 'split-' + str(i) + '.txt', 'synthetic\n')
                 for i in range(8)]
        items = [tooling.enqueue(root, self.fdir, 'main') for root in roots]
        original = flow.pre_push_checks
        checked = []
        def checks(root, commit, *args, **kwargs):
            checked.append(commit)
            if (Path(root) / 'split-2.txt').exists():
                raise flow.FlowError('synthetic bisect failure')
            return original(root, commit, *args, **kwargs)
        with patch.object(flow, 'pre_push_checks', side_effect=checks):
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        bisect = result['bisection']
        self.assertEqual(bisect['max_rounds'], 3)
        self.assertEqual(max(trial['round'] for trial in bisect['trials']), 3)
        self.assertEqual(len(checked), 8)  # full batch, baseline, two probes per split level
        self.assertEqual(checked[-1], result['integrated']['commit'])
        self.assertEqual(result['tooling_dropped'][0]['revision'], items[2]['revision'])
        tree = Path(result['tree'])
        for i in range(8):
            self.assertEqual((tree / ('split-' + str(i) + '.txt')).exists(), i != 2)
        with self.assertRaisesRegex(flow.FlowError, 'synthetic bisect failure'):
            lane.publish_tooling(roots[2], self.fdir, python=sys.executable, ci_wait=0, wait_lane=True)

    def test_multiple_failing_inputs_and_all_bad_batch_exit_with_receipts(self):
        roots = [self.other('bad-' + str(i), 'bad-' + str(i) + '.txt', 'synthetic\n')
                 for i in range(3)]
        items = [tooling.enqueue(root, self.fdir, 'main') for root in roots]
        before = git(self.repo.origin, 'rev-parse', 'main')
        original = flow.pre_push_checks
        def checks(root, *args, **kwargs):
            if list(Path(root).glob('bad-*.txt')): raise flow.FlowError('synthetic all bad')
            return original(root, *args, **kwargs)
        with patch.object(flow, 'pre_push_checks', side_effect=checks):
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        self.assertEqual(result['state'], 'done')
        self.assertIsNone(result['integrated'])
        self.assertEqual(git(self.repo.origin, 'rev-parse', 'main'), before)
        self.assertEqual(len(result['tooling_dropped']), 3)
        self.assertLessEqual(max(t['round'] for t in result['bisection']['trials']), 2)
        for root in roots:
            with self.assertRaisesRegex(flow.FlowError, 'bounced:'):
                lane.publish_tooling(root, self.fdir, python=sys.executable, ci_wait=0, wait_lane=True)

    def test_build_failure_is_bisected_without_discarding_good_input(self):
        roots = [self.other('build-' + str(i), 'build-' + str(i) + '.txt', 'synthetic\n')
                 for i in range(2)]
        for root in roots: tooling.enqueue(root, self.fdir, 'main')
        original = lane.build
        def build(*args, **kwargs):
            tree = original(*args, **kwargs)
            if tree and (tree / 'build-0.txt').exists(): raise flow.FlowError('synthetic staged check failure')
            return tree
        with patch.object(lane, 'build', side_effect=build):
            result = lane.run_lane(self.root, self.fdir, python=sys.executable, ci_wait=0)
        self.assertEqual(result['state'], 'done')
        self.assertEqual(len(result['tooling_accepted']), 1)
        self.assertTrue((Path(result['tree']) / 'build-1.txt').exists())
        self.assertFalse((Path(result['tree']) / 'build-0.txt').exists())
