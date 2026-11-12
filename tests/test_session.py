"""Tests for verifier sessions and start accounting against a fake `boat` CLI (no Boat account used).

The fake keeps its machines in a JSON file, answers the CLI calls the verifier tools make and
counts create, fork and resume as starts, as Boat does.
"""
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
sys.path.insert(0, str(ROOT / 'tools'))
import boatctl  # noqa: E402
import pipeline  # noqa: E402
import starts  # noqa: E402
import vsession  # noqa: E402
import confirm_session  # noqa: E402

TARGET = json.loads((ROOT / 'builds/target.json').read_text())

# Start counters as `boat limits --json` printed them on a trial account (other fields omitted).
RECORDED_LIMITS = {
    "accessTier": "trial", "activeSandboxes": 1, "maxActiveSandboxes": 2, "sandboxPlanKey": "trial",
    "creditUsedSeconds": 8857, "trialComputeUsedSeconds": 8857,
    "startLimits": {"perDay": 75, "perHour": 25, "perMinute": 5},
    "starts": {"day": {"limit": 75, "remaining": 32, "used": 43}, "hour": {"limit": 25, "remaining": 5, "used": 20},
               "minute": {"limit": 5, "remaining": 5, "used": 0}, "unlimited": False},
}

FAKE_BOAT = r'''#!PYTHON
import fcntl, json, os, sys
from datetime import datetime, timedelta, timezone
path = os.environ['FAKE_BOAT_STATE']
lock = open(path + '.lock', 'w')
fcntl.flock(lock, fcntl.LOCK_EX)
st = json.load(open(path))
args = sys.argv[1:]
st['calls'].append(args)
def iso(sec):
    return (datetime.now(timezone.utc) + timedelta(seconds=sec)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
def save():
    json.dump(st, open(path, 'w'))
def start():
    for w in ('day', 'hour', 'minute'):
        st['starts'][w]['used'] += 1
        st['starts'][w]['remaining'] -= 1
    st['started'] += 1
def flag(name, default=None):
    return args[args.index(name) + 1] if name in args else default
cmd = args[0]
m = st['machines'].get(args[1]) if len(args) > 1 else None
out = {}
if cmd == 'limits':
    out = {'starts': st['starts'], 'sandboxPlanKey': 'trial', 'activeSandboxes':
           sum(1 for x in st['machines'].values() if x['state'] == 'idle'), 'maxActiveSandboxes': 2,
           'creditUsedSeconds': 100, 'trialComputeUsedSeconds': 100}
elif cmd == 'list':
    out = {'sandboxes': [{'id': k, 'name': v['name'], 'state': v['state']} for k, v in st['machines'].items()]}
elif cmd == 'info':
    out = {'sandbox': {'id': args[1], 'state': m['state'], 'archiveAfter': m.get('deadline'),
                       'stoppedAt': m.get('stoppedAt'), 'stop': None, 'vcpu': 4}}
elif cmd == 'resume':
    start(); m['state'] = 'idle'; m['deadline'] = iso(int(flag('--ttl', 3600)))
elif cmd == 'fork':
    start(); new = 'bx_fork%d' % st['started']
    st['machines'][new] = {'name': 'fork', 'state': 'idle', 'deadline': iso(1800), 'usage': 0, 'markers': []}
    print(json.dumps({'event': 'ready', 'id': new})); save(); sys.exit(0)
elif cmd == 'extend':
    m['deadline'] = iso(int(flag('--ttl')))
elif cmd == 'stop':
    m['state'] = 'stopped'; m['deadline'] = None; m['usage'] += 30
elif cmd == 'usage':
    out = {'seconds': m['usage']}
elif cmd == 'exec':
    line = args[args.index('--') + 1]
    stdout = ''
    if 'TOOLCHAIN' in line:
        stdout = 'TOOLCHAIN=ok\nIMAGE=%s\nCPUS=4\n' % st['image']
    elif '.running' in line and 'ls -d' in line:
        stdout = ''.join('/home/user/tasks/%s/.running\n' % t for t in m.get('markers', []))
    out = {'exitCode': 0, 'stdout': stdout, 'stderr': ''}
elif cmd in ('scp', 'rename', 'delete'):
    out = {}
else:
    print('fake boat: unsupported ' + cmd, file=sys.stderr); save(); sys.exit(2)
save()
print(json.dumps(out))
'''


class FakeBoat(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.state_path = self.tmp / 'boat.json'
        script = self.tmp / 'boat'
        script.write_text(FAKE_BOAT.replace('#!PYTHON', '#!' + sys.executable))
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        self.patches = [mock.patch.object(boatctl, 'BOAT', str(script)),
                        mock.patch.dict(os.environ, {'FAKE_BOAT_STATE': str(self.state_path),
                                                     'SR_VERIFIER_STATE': str(self.tmp / 'state'),
                                                     'SR_STARTS_RESERVE': '10'}),
                        mock.patch.object(vsession, 'local_image', lambda: None)]
        for p in self.patches:
            p.start()
        os.environ.pop('SR_STARTS_FORCE', None)
        os.environ.pop('SR_SESSION_ID', None)
        self.write_state(a='idle', b='stopped')

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        os.environ.pop('SR_SESSION_ID', None)
        shutil.rmtree(self.tmp)

    def write_state(self, a, b, day_left=50, hour_left=20, image=None):
        from datetime import datetime, timedelta, timezone
        later = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        machines = {'bx_a': {'name': vsession.NAMES['a'], 'state': a, 'usage': 1000, 'markers': [],
                             'deadline': later if a == 'idle' else None},
                    'bx_b': {'name': vsession.NAMES['b'], 'state': b, 'usage': 200, 'markers': [],
                             'deadline': later if b == 'idle' else None}}
        st = {'machines': machines, 'calls': [], 'started': 0, 'image': image or TARGET['image_sha256'],
              'starts': {'day': {'limit': 75, 'used': 75 - day_left, 'remaining': day_left},
                         'hour': {'limit': 25, 'used': 25 - hour_left, 'remaining': hour_left},
                         'minute': {'limit': 5, 'used': 0, 'remaining': 5}, 'unlimited': False}}
        self.state_path.write_text(json.dumps(st))

    def state(self):
        return json.loads(self.state_path.read_text())

    def edit(self, fn):
        st = self.state()
        fn(st)
        self.state_path.write_text(json.dumps(st))

    def quiet(self, *_):
        pass

    def test_up_is_idempotent_and_costs_at_most_one_start_per_machine(self):
        deadline = self.state()['machines']['bx_a']['deadline']
        vsession.up(log=self.quiet)
        self.assertEqual(self.state()['started'], 1)  # B resumed, A reused
        self.assertEqual(self.state()['machines']['bx_a']['deadline'], deadline)  # A's deadline untouched
        vsession.up(log=self.quiet)
        self.assertEqual(self.state()['started'], 1)
        self.assertEqual(len(starts.logged()), 1)
        session = vsession.load()
        self.assertEqual(session['state'], 'up')
        self.assertEqual({k: e['toolchain'] for k, e in session['machines'].items()}, {'a': 'ok', 'b': 'ok'})
        self.assertEqual({k: e['image'] for k, e in session['machines'].items()}, {'a': 'ok', 'b': 'ok'})

    def test_up_from_cold_resumes_each_machine_once(self):
        self.write_state(a='stopped', b='stopped')
        vsession.up(log=self.quiet)
        resumes = [c[1] for c in self.state()['calls'] if c[0] == 'resume']
        self.assertEqual(sorted(resumes), ['bx_a', 'bx_b'])

    def test_up_refuses_when_reserve_would_be_used(self):
        self.write_state(a='stopped', b='stopped', day_left=11)
        with self.assertRaises(starts.StartsRefused):
            vsession.up(log=self.quiet)
        self.assertEqual(self.state()['started'], 0)
        vsession.up(force=True, log=self.quiet)
        self.assertEqual(self.state()['started'], 2)

    def test_image_mismatch_leaves_session_unverified(self):
        self.write_state(a='idle', b='idle', image='0' * 64)
        with self.assertRaises(boatctl.BoatError):
            vsession.up(log=self.quiet)
        self.assertEqual(vsession.load()['machines']['b']['state'], 'unverified')

    def test_down_refuses_while_a_task_is_marked_running(self):
        vsession.up(log=self.quiet)
        self.edit(lambda st: st['machines']['bx_a'].__setitem__('markers', ['triage-x']))
        with self.assertRaises(vsession.SessionBusy):
            vsession.down(log=self.quiet)
        self.assertEqual(self.state()['machines']['bx_b']['state'], 'idle')
        booked = []
        vsession.down(only='b', log=self.quiet, record=lambda s, n: booked.append((s, n)))
        st = self.state()
        self.assertEqual((st['machines']['bx_a']['state'], st['machines']['bx_b']['state']), ('idle', 'stopped'))
        self.assertEqual(vsession.load()['state'], 'up')
        self.assertEqual(booked, [(30, None)])
        vsession.down(force=True, log=self.quiet, record=lambda s, n: booked.append((s, n)))
        self.assertEqual(vsession.load()['state'], 'down')
        self.assertEqual(booked[-1][1], 1)

    def test_attempt_in_session_never_starts_a_machine(self):
        vsession.up(log=self.quiet)
        before = self.state()['started']
        machine, how = pipeline.ensure_standing()
        self.assertEqual((machine, self.state()['started']), ('bx_a', before))
        self.assertIn('session A', how)
        self.edit(lambda st: st['machines']['bx_a'].__setitem__('state', 'stopped'))
        with self.assertRaises(boatctl.BoatError):
            pipeline.ensure_standing()
        self.assertEqual(self.state()['started'], before)

    def test_confirm_in_session_mode_performs_zero_starts(self):
        vsession.up(log=self.quiet)
        before = self.state()['started']
        task_dir = self.tmp / '.local' / 'tasks' / 'demo-task'
        task_dir.mkdir(parents=True)
        task = {'dir': task_dir, 'task_id': 'demo-task', 'build_id': TARGET['build_id'],
                'compiled': 'reconstruction/x/Y.cpp', 'recipe': 'reconstruction/recipes/msvc-19.16.27054-o2.json',
                'functions': [{'rva': 0x10, 'size': 4, 'symbol': 'f'}], 'symbols_repo': 'm.json'}
        used = []

        class FakeHost:
            def __init__(self, machine, label, remote_dir, task, **_):
                self.machine, self.label = machine, label
                used.append(machine)

            def run(self, files, stage, fresh=False):
                return 0, ''

            def fetch(self, dest):
                Path(dest).mkdir(parents=True, exist_ok=True)
                return Path(dest)

        base = mock.Mock()
        base.result_of.return_value = ('fail', 'byte-mismatch')
        base.mac_compare.return_value = (1, task_dir / 'none.json')
        with mock.patch.object(confirm_session, 'prepare', lambda b, d, r, o: (task, {}, [])), \
                mock.patch.object(pipeline, 'Host', FakeHost), \
                mock.patch.object(pipeline, 'load_config', lambda d: {}), \
                mock.patch.object(pipeline, 'record_cost', lambda *a: None):
            code = confirm_session.run(base, [str(task_dir)], log=self.quiet)
        self.assertEqual(code, 1)  # every run failed in this fake, so nothing is written
        self.assertEqual(sorted(used), ['bx_a', 'bx_b'])
        self.assertEqual(self.state()['started'], before)
        self.assertFalse([c for c in self.state()['calls'] if c[0] in ('resume', 'fork', 'new', 'stop')][before:])

    def test_down_keep_releases_a_without_stopping_it(self):
        self.write_state(a='idle', b='stopped')
        vsession.up(log=self.quiet)
        self.assertEqual(self.state()['started'], 1)
        # Another agent's task on A must not block a session end that keeps A running.
        self.edit(lambda st: st['machines']['bx_a'].__setitem__('markers', ['other-task']))
        booked = []
        vsession.down(keep=['a'], log=self.quiet, record=lambda s, n: booked.append((s, n)))
        st = self.state()
        self.assertEqual((st['machines']['bx_a']['state'], st['machines']['bx_b']['state']), ('idle', 'stopped'))
        self.assertEqual([c[1] for c in st['calls'] if c[0] == 'stop'], ['bx_b'])
        session = vsession.load()
        self.assertEqual(session['state'], 'down')
        self.assertTrue(session['machines']['a']['left_running'])
        self.assertEqual(booked, [(30, 1)])  # B's stop only; shared A is not session overhead
        with self.assertRaises(boatctl.BoatError):
            vsession.down(only='a', keep=['a'], log=self.quiet)

    def test_down_after_partial_down_does_not_book_a_machine_twice(self):
        vsession.up(log=self.quiet)
        booked = []
        vsession.down(only='b', log=self.quiet, record=lambda s, n: booked.append(s))
        vsession.down(keep=['a'], log=self.quiet, record=lambda s, n: booked.append(s))
        self.assertEqual(booked, [30, 0])
        self.assertEqual([c[1] for c in self.state()['calls'] if c[0] == 'stop'], ['bx_b'])

    def test_batch_confirm_runs_every_unit_on_a_then_b_with_no_starts(self):
        vsession.up(log=self.quiet)
        before = self.state()['started']
        tasks = []
        for name in ('unit-one', 'unit-two'):
            d = self.tmp / '.local' / 'tasks' / name
            d.mkdir(parents=True)
            tasks.append({'dir': d, 'task_id': name, 'build_id': TARGET['build_id'],
                          'compiled': f'reconstruction/x/{name}.cpp',
                          'recipe': 'reconstruction/recipes/msvc-19.16.27054-o2.json',
                          'functions': [{'rva': 0x10 + len(tasks), 'size': 4, 'symbol': 'f'}],
                          'symbols_repo': 'm.json'})
        by_dir = {str(t['dir']): t for t in tasks}
        ran = []

        class FakeHost:
            def __init__(self, machine, label, remote_dir, task, **_):
                self.machine, self.label, self.task = machine, label, task['task_id']

            def run(self, files, stage, fresh=False):
                ran.append((self.task, self.label, self.machine))
                return 0, ''

            def fetch(self, dest):
                Path(dest).mkdir(parents=True, exist_ok=True)
                return Path(dest)

        base = mock.Mock()
        base.result_of.return_value = ('fail', 'byte-mismatch')
        base.mac_compare.return_value = (1, self.tmp / 'none.json')
        out = []
        with mock.patch.object(confirm_session, 'prepare', lambda b, d, r, o: (by_dir[d], {}, [])), \
                mock.patch.object(pipeline, 'Host', FakeHost), \
                mock.patch.object(pipeline, 'load_config', lambda d: {}), \
                mock.patch.object(pipeline, 'record_cost', lambda *a: None):
            code = confirm_session.run(base, list(by_dir), log=out.append)
        self.assertEqual(code, 1)
        self.assertEqual(sorted(ran), [('unit-one', 'boat-verifier-a', 'bx_a'), ('unit-one', 'boat-verifier-b', 'bx_b'),
                                       ('unit-two', 'boat-verifier-a', 'bx_a'), ('unit-two', 'boat-verifier-b', 'bx_b')])
        self.assertEqual([h[0] for h in vsession.hosts()], ['a', 'b'])  # first pass A, second B
        self.assertEqual(self.state()['started'], before)
        self.assertEqual(sum('NOT REPRODUCED' in line for line in out), 2)

    def test_confirm_without_session_refuses(self):
        with self.assertRaises(pipeline.PipelineError):
            confirm_session.run(mock.Mock(), ['x'], log=self.quiet)
        self.assertEqual(self.state()['started'], 0)

    def test_reserve_blocks_a_fork(self):
        self.write_state(a='stopped', b='stopped', day_left=10)
        with self.assertRaises(boatctl.BoatError) as ctx:
            boatctl.fork('bx_a', 'sr-x-confirm', 1800)
        self.assertIn('reserve', str(ctx.exception))
        self.assertEqual([c for c in self.state()['calls'] if c[0] == 'fork'], [])
        self.write_state(a='stopped', b='stopped', day_left=11)
        boatctl.fork('bx_a', 'sr-x-confirm', 1800)
        self.assertEqual(self.state()['started'], 1)
        self.assertEqual(starts.logged()[0]['reason'], 'fork')

    def test_status_warns_about_retention(self):
        self.edit(lambda st: st['machines']['bx_b'].__setitem__('stoppedAt', '2000-01-01T00:00:00.000Z'))
        warnings = vsession.status(log=self.quiet)
        self.assertTrue(any(vsession.NAMES['b'] in w for w in warnings))


class Counters(unittest.TestCase):
    def test_recorded_limits_sample(self):
        c = starts.parse(RECORDED_LIMITS)
        self.assertEqual(c['day'], {'limit': 75, 'used': 43, 'remaining': 32})
        self.assertEqual(c['hour'], {'limit': 25, 'used': 20, 'remaining': 5})
        self.assertEqual((c['plan'], c['active'], c['max_active']), ('trial', 1, 2))
        self.assertIsNone(starts.check(c, 1, reserve=10))
        self.assertIn('left this', starts.check(c, 6, reserve=10))
        self.assertIn('reserve', starts.check(dict(c, hour={'limit': 25, 'used': 0, 'remaining': 25},
                                                   minute={'limit': 50, 'used': 0, 'remaining': 50}), 23, reserve=10))
        self.assertIn('32 left', starts.line(c))

    def test_paid_plan_limits(self):
        paid = {'sandboxPlanKey': 'plan-20', 'activeSandboxes': 2, 'maxActiveSandboxes': 100,
                'starts': {'day': {'limit': 200, 'used': 189}, 'hour': {'limit': 60, 'used': 3},
                           'minute': {'limit': 12, 'used': 0}, 'unlimited': False}}
        c = starts.parse(paid)
        self.assertEqual((c['day']['remaining'], c['hour']['remaining'], c['minute']['remaining']), (11, 57, 12))
        self.assertIsNone(starts.check(c, 1, reserve=10))
        self.assertIn('reserve', starts.check(c, 2, reserve=10))
        self.assertIsNone(starts.check(dict(c, unlimited=True), 50, reserve=10))

    def test_minute_window_is_never_forced(self):
        c = starts.parse(dict(RECORDED_LIMITS, starts=dict(RECORDED_LIMITS['starts'],
                                                           minute={'limit': 5, 'used': 5, 'remaining': 0})))
        self.assertIn('minute', starts.check(c, 1, force=True))


if __name__ == '__main__':
    unittest.main()
