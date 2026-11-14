"""Synthetic SSH admission/retry tests: no network, compiler or game inputs."""
import argparse
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/verifier'))
import host_agent  # noqa: E402
import runners  # noqa: E402


def host(**over):
    return dict({'backend': 'ssh', 'host_id': 'test-native', 'machine': 'test-pc',
                 'loader': 'native', 'ssh_config': 'test-config', 'ssh_host': 'test-host',
                 'python': ['python3'], 'msvc': 'C:/test/compiler', 'image': 'C:/test/image',
                 'work': 'C:/test/work', 'max_parallel': 8}, **over)


def proc(code, stderr='', stdout=''):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class Retry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        patch = mock.patch.dict(os.environ, SR_VERIFIER_STATE=self.tmp.name)
        patch.start()
        self.addCleanup(patch.stop)
        self.messages = []
        self.transport = runners.SshTransport(host(), log=self.messages.append)

    def events(self):
        return [json.loads(line) for line in (self.state / 'transport-errors.jsonl').read_text().splitlines()]

    def test_ssh_connection_failure_retries_same_command_then_returns_mismatch_once(self):
        with mock.patch.object(runners.subprocess, 'run', side_effect=[proc(255), proc(1, 'connection reset')]) as call, \
                mock.patch.object(runners.time, 'sleep') as sleep:
            self.assertEqual(self.transport.run(['python3', 'run.py'], 10)[0], 1)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(call.call_args_list[0], call.call_args_list[1])
        sleep.assert_called_once_with(1)
        self.assertEqual([e['kind'] for e in self.events()], ['transport_error'])
        self.assertEqual(len(self.messages), 1)

    def test_comparator_mismatch_and_build_refusals_never_retry(self):
        for code in (1, 3, 42, 43, 44, 45):
            with self.subTest(code=code), mock.patch.object(runners.subprocess, 'run', return_value=proc(code, 'connection reset')) as call, \
                    mock.patch.object(runners.time, 'sleep') as sleep:
                self.assertEqual(self.transport.run(['python3', 'run.py'], 10)[0], code)
                call.assert_called_once()
                sleep.assert_not_called()
        self.assertFalse((self.state / 'transport-errors.jsonl').exists())

    def test_scp_upload_and_download_retry_reset_and_255(self):
        with mock.patch.object(runners.subprocess, 'run', side_effect=[proc(1, 'Connection reset by peer'), proc(0),
                                                                    proc(255, 'Connection closed'), proc(0)]) as call, \
                mock.patch.object(runners.time, 'sleep'):
            self.transport.put(['bundle.tar', 'agent.py'], 'C:/test/work')
            self.transport.get('C:/test/work/result.tar', 'result.tar')
        self.assertEqual(call.call_count, 4)
        self.assertEqual([e['operation'] for e in self.events()], ['scp', 'scp'])
        self.assertTrue(all(e['host_id'] == 'test-native' for e in self.events()))
        self.assertNotIn('C:/', (self.state / 'transport-errors.jsonl').read_text())

    def test_three_attempt_bound_and_backoff_and_release(self):
        with mock.patch.object(runners.subprocess, 'run', return_value=proc(255)) as call, \
                mock.patch.object(runners.time, 'sleep') as sleep:
            with self.assertRaisesRegex(runners.TransportError, 'transport error after 3 attempts'):
                self.transport.run(['python3', 'batch.py'], 10)
        self.assertEqual(call.call_count, 3)
        self.assertEqual(sleep.call_args_list, [mock.call(1), mock.call(2)])
        self.assertEqual([e['attempt'] for e in self.events()], [1, 2, 3])
        self.assertEqual(runners.slots_busy('test-native', 4, directory=self.state / 'runner-sessions'), 0)

    def test_os_reset_retries_but_unrelated_scp_errors_do_not(self):
        with mock.patch.object(runners.subprocess, 'run', side_effect=[ConnectionResetError(errno.ECONNRESET, 'reset'), proc(0)]), \
                mock.patch.object(runners.time, 'sleep'):
            self.transport.put(['bundle.tar'], 'remote')
        self.assertEqual(self.events()[0]['reason'], 'connection reset')
        with mock.patch.object(runners.subprocess, 'run', return_value=proc(1, 'Permission denied')) as call:
            with self.assertRaisesRegex(runners.RunnerError, 'scp failed'):
                self.transport.get('remote', 'local')
            call.assert_called_once()

    def test_timeout_does_not_repeat_a_remote_execution_and_releases_session(self):
        with mock.patch.object(runners.subprocess, 'run', side_effect=subprocess.TimeoutExpired('ssh', 5)) as call:
            self.assertEqual(self.transport.run(['python3', 'run.py'], 5), (124, '', 'timeout'))
            call.assert_called_once()
        self.assertEqual(runners.slots_busy('test-native', 4, directory=self.state / 'runner-sessions'), 0)

    def test_fetch_keeps_transport_error_classification(self):
        transport = mock.Mock()
        transport.get.side_effect = runners.TransportError('test-native: scp transport error')
        worker = runners.AgentHost(host(), {'task_id': 'test-unit'}, transport=transport)
        worker._run = 'test-unit-0123456789ab'
        with self.assertRaisesRegex(runners.TransportError, 'scp transport error'):
            worker.fetch(self.state / 'results')

    def test_shared_config_parent_is_used_by_independent_checkouts(self):
        with mock.patch.dict(os.environ, SR_RUNNERS_CONFIG=str(self.state / 'shared/runners.json')):
            with mock.patch.dict(os.environ) as env:
                env.pop('SR_VERIFIER_STATE', None)
                self.assertEqual(runners.SshTransport(host()).state, (self.state / 'shared').resolve())


class Admission(unittest.TestCase):
    def test_default_and_config_validation(self):
        raw = {'runners_schema': 1, 'attempt': 'pc', 'confirm': [], 'hosts': {'pc': host()}}
        self.assertEqual(runners.validate(raw)['hosts']['pc']['max_sessions'], 4)
        raw['hosts']['pc']['max_sessions'] = 2
        self.assertEqual(runners.validate(raw)['hosts']['pc']['max_sessions'], 2)
        for bad in (0, 65, True, '4'):
            raw['hosts']['pc']['max_sessions'] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(runners.RunnerError, 'max_sessions'):
                runners.validate(raw)

    def test_ssh_and_scp_share_limit_across_six_processes(self):
        # Every child has its own transport object and Python interpreter. Its fake subprocess
        # records active SSH/scp lifetimes; the actual cross-process flock admission is real.
        child = r'''
import json, os, pathlib, subprocess, sys, time
sys.path.insert(0, sys.argv[1])
import runners
state = pathlib.Path(os.environ['SR_VERIFIER_STATE'])
host = json.loads(sys.argv[2])
t = runners.SshTransport(host)
number = sys.argv[3]
def record(kind):
    with open(state / 'events.jsonl', 'a') as f:
        f.write(json.dumps([kind, os.getpid()]) + '\n')
def execute(*args, **kwargs):
    record('start')
    time.sleep(0.07)
    record('end')
    return subprocess.CompletedProcess([], 0, '', '')
runners.subprocess.run = execute
(state / ('ready-' + number)).touch()
while not (state / 'go').exists():
    time.sleep(0.005)
for _ in range(2):
    if int(number) % 3 == 0:
        t.run(['python3', 'agent.py'], 10)
    elif int(number) % 3 == 1:
        t.put(['bundle.tar'], 'remote')
    else:
        t.get('remote', 'local')
'''
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            env = dict(os.environ, SR_VERIFIER_STATE=tmp)
            children = [subprocess.Popen([sys.executable, '-c', child, str(ROOT / 'tools/verifier'),
                                          json.dumps(host(max_sessions=2)), str(i)], env=env,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(6)]
            try:
                deadline = time.monotonic() + 15
                while len(list(state.glob('ready-*'))) < 6 and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertEqual(len(list(state.glob('ready-*'))), 6)
                (state / 'go').touch()
                for p in children:
                    out, err = p.communicate(timeout=15)
                    self.assertEqual(p.returncode, 0, (out, err))
                active, peak = set(), 0
                events = [json.loads(line) for line in (state / 'events.jsonl').read_text().splitlines()]
                for kind, pid in events:
                    if kind == 'start':
                        active.add(pid)
                    else:
                        active.remove(pid)
                    peak = max(peak, len(active))
                    self.assertLessEqual(len(active), 2)
                self.assertEqual((len(events), peak, active), (24, 2, set()))
            finally:
                for p in children:
                    if p.poll() is None:
                        p.kill()
                    p.communicate()


class NoRepeatedComparison(unittest.TestCase):
    def test_reconnected_agent_refuses_run_and_batch_after_a_mismatch(self):
        # The first execution exits 1. A second execution would change its result to 0.
        # Both command forms must refuse before invoking that stub again.
        for command in ('run', 'batch'):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                name = 'test-unit-0123456789ab'
                run = root / name
                bundle = root / (name + '.tar')
                prefix = 'unit-one/' if command == 'batch' else ''
                counter = root / 'executions'
                source = (f'import pathlib,sys\np=pathlib.Path({str(counter)!r})\n'
                          'n=int(p.read_text()) if p.exists() else 0\np.write_text(str(n+1))\n'
                          'sys.exit(1 if n == 0 else 0)\n').encode()
                with tarfile.open(bundle, 'w') as tar:
                    contents = {prefix + 'repo/tools/verifier/unit_build.py': source}
                    if command == 'batch':
                        contents['units.json'] = b'["unit-one"]'
                    for filename, data in contents.items():
                        info = tarfile.TarInfo(filename)
                        info.size = len(data)
                        tar.addfile(info, io.BytesIO(data))
                args = argparse.Namespace(run=str(run), bundle=str(bundle), msvc='compiler', image='image',
                                          loader='native', label='test-native', jobs=1)
                fn = host_agent.cmd_batch if command == 'batch' else host_agent.cmd_run
                with mock.patch('sys.stdout', new=io.StringIO()):
                    self.assertEqual(fn(args), 0 if command == 'batch' else 1)
                if command == 'batch':
                    with tarfile.open(root / (name + '.out.tar')) as tar:
                        self.assertEqual(json.load(tar.extractfile('unit-one.agent.json'))['exit'], 1)
                with self.assertRaisesRegex(host_agent.AgentRefusal, 'refusing duplicate execution'):
                    fn(args)
                self.assertEqual(counter.read_text(), '1')
