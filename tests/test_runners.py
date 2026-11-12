"""Tests for tools/verifier/runners.py, host_agent.py and the loader paths of unit_build.py.

The ssh backend is exercised against a stub transport that runs the host side on this machine
but insists on everything an ssh command line must satisfy (plain tokens, no file content), and
the whole compile-and-compare path runs with the fake msvc-wine compiler of test_unit_build.py
and the original synthetic COFF/PE fixtures. No network, compiler, Wine or game input.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
sys.path.insert(0, str(ROOT / 'tools'))
import synthetic_pecoff as sp  # noqa: E402
import runners  # noqa: E402
import unit_build as ub  # noqa: E402
import confirm_runners  # noqa: E402
import pipeline  # noqa: E402
import source_digest  # noqa: E402
from test_unit_build import FAKE_CL, sha  # noqa: E402


def host(**over):
    h = {'backend': 'local', 'host_id': 'mac-wine', 'machine': 'maintainer-mac', 'loader': 'wine',
         'msvc': '/opt/msvc', 'work': '/opt/work', 'wine_bin': '/opt/wine/bin', 'wineprefix': '/opt/prefix',
         'image': '/opt/SkyrimSE.exe', 'max_parallel': 2}
    h.update(over)
    return h


def ssh_host(**over):
    h = {'backend': 'ssh', 'host_id': 'winpc-native', 'machine': 'maintainer-winpc', 'loader': 'native',
         'ssh_config': '.local/winpc/ssh_config', 'ssh_host': 'winpc', 'python': ['py', '-3.12'],
         'msvc': 'C:/sr-test/msvc', 'image': 'C:/sr-test/private/SkyrimSE.exe', 'work': 'C:/sr-test/work',
         'max_parallel': 4}
    h.update(over)
    return h


def config(**over):
    c = {'runners_schema': 1, 'attempt': 'mac', 'confirm': ['mac', 'winpc'],
         'hosts': {'boat': {'backend': 'boat'}, 'mac': host(), 'winpc': ssh_host()}}
    c.update(over)
    return c


class Config(unittest.TestCase):
    def test_valid_config_resolves_local_paths_against_the_checkout(self):
        c = runners.validate(config(hosts={'mac': host(msvc='.local/toolchains/msvc', work='.local/w'),
                                           'winpc': ssh_host()}), root='/repo')
        self.assertEqual(c['hosts']['mac']['msvc'], '/repo/.local/toolchains/msvc')
        self.assertEqual(c['hosts']['winpc']['ssh_config'], '/repo/.local/winpc/ssh_config')
        self.assertEqual(c['hosts']['winpc']['msvc'], 'C:/sr-test/msvc')
        self.assertEqual(c['attempt'], 'mac')
        # An ssh host gets units in batches by default; a local host one at a time.
        self.assertEqual((c['hosts']['mac']['batch'], c['hosts']['winpc']['batch']), (1, 8))

    def test_rejections(self):
        cases = [
            (dict(runners_schema=2), 'runners_schema'),
            (dict(hosts={}), 'at least one host'),
            (dict(hosts={'mac': host(host_id='Mac/Path')}), 'host_id'),
            (dict(hosts={'mac': host(), 'winpc': ssh_host(host_id='mac-wine')}), 'used twice'),
            (dict(hosts={'mac': host(machine=None)}), 'machine'),
            (dict(hosts={'mac': host(loader='rosetta')}), 'loader'),
            (dict(hosts={'mac': host(max_parallel=0)}), 'max_parallel'),
            (dict(hosts={'mac': host(batch=0)}), 'batch'),
            (dict(hosts={'mac': host(), 'winpc': ssh_host(batch=True)}), 'batch'),
            (dict(hosts={'mac': host(), 'winpc': ssh_host(msvc='C:/Program Files/msvc')}), 'quoting'),
            (dict(hosts={'mac': host(), 'winpc': ssh_host(image='C:/x;rm -rf')}), 'quoting'),
            (dict(hosts={'mac': host(), 'winpc': ssh_host(ssh_host=None)}), 'ssh_host'),
            (dict(attempt='nowhere'), 'not a host'),
            (dict(confirm=['boat']), 'runner hosts only'),
        ]
        for over, words in cases:
            raw = config(**over)
            if 'hosts' in over and over['hosts'] and 'boat' not in over['hosts']:
                raw['attempt'], raw['confirm'] = next(iter(over['hosts'])), []
            with self.subTest(words=words), self.assertRaises(runners.RunnerError) as cm:
                runners.validate(raw, root='/repo')
            self.assertIn(words, str(cm.exception))

    def test_missing_file_means_boat(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(runners.load(Path(tmp) / 'runners.json'))
            path = Path(tmp) / 'runners.json'
            path.write_text(json.dumps(config(attempt='boat')))
            self.assertIsNone(runners.for_attempt(runners.load(path, root=tmp)))
            path.write_text(json.dumps(config()))
            chosen = runners.for_attempt(runners.load(path, root=tmp))
            self.assertEqual((chosen['host_id'], chosen['backend']), ('mac-wine', 'local'))

    def test_example_config_is_valid(self):
        example = json.loads((ROOT / 'tools/verifier/runners.example.json').read_text())
        c = runners.validate(example, root='/repo')
        self.assertEqual(sorted(h['backend'] for h in c['hosts'].values()), ['boat', 'local', 'ssh'])

    def test_describe_names_no_paths(self):
        line = runners.describe(runners.validate(config(), root='/repo')['hosts']['winpc'])
        self.assertEqual(line, 'winpc-native (machine maintainer-winpc, ssh, native)')


class Independence(unittest.TestCase):
    def test_rule(self):
        mac, pc = host(), ssh_host()
        self.assertIsNone(runners.independence_problem([mac, pc]))
        self.assertIn('two compile hosts', runners.independence_problem([mac]))
        self.assertIn('one machine', runners.independence_problem([mac, ssh_host(machine='maintainer-mac')]))
        self.assertIn('loaders', runners.independence_problem([mac, ssh_host(loader='wine')]))
        # What the hosts reported decides, not what the config claims.
        facts = {'mac-wine': {'loader': 'wine'}, 'winpc-native': {'loader': 'wine'}}
        self.assertIn('loaders', runners.independence_problem([mac, pc], facts))
        self.assertIn('loaders', runners.independence_problem([mac, pc], {'mac-wine': {'loader': 'wine'}}))

    def test_for_confirm_refuses_dependent_hosts(self):
        c = runners.validate(config(hosts={'mac': host(), 'mac2': host(host_id='mac-wine-2', loader='native')},
                                    attempt='mac', confirm=['mac', 'mac2']), root='/repo')
        with self.assertRaises(runners.RunnerError):
            runners.for_confirm(c)


class ReportedFacts(unittest.TestCase):
    """The hosts' own reports, not the config, decide loader and OS."""

    def facts(self, **over):
        f = {'mac-wine': {'os': 'macos', 'loader': 'wine', 'toolchain_check': 'checked'},
             'winpc-native': {'os': 'windows', 'loader': 'native', 'toolchain_check': 'checked'}}
        for k, v in over.items():
            f[k.replace('_', '-')] = dict(f[k.replace('_', '-')], **v)
        return f

    def test_os_and_loader_cross_checks(self):
        hosts = [host(), ssh_host()]
        self.assertIsNone(runners.independence_problem(hosts, self.facts()))
        self.assertIn('not windows', runners.independence_problem(hosts, self.facts(winpc_native={'os': 'macos'})))
        self.assertIn('two different operating systems',
                      runners.independence_problem(hosts, self.facts(mac_wine={'os': 'windows'})))
        self.assertIn('two different operating systems',
                      runners.independence_problem(hosts, self.facts(mac_wine={'os': None})))
        # A config naming a loader the host does not report is refused even if the pair still differs.
        swapped = [host(loader='native'), ssh_host(loader='wine')]
        self.assertIn('its config names', runners.independence_problem(swapped, self.facts()))

    def test_record_needs_a_toolchain_check_made_in_this_run(self):
        hosts = [host(), ssh_host()]
        self.assertIsNone(confirm_runners.facts_problem(hosts, self.facts()))
        for state in ('cached', None):
            with self.subTest(state=state):
                problem = confirm_runners.facts_problem(hosts, self.facts(winpc_native={'toolchain_check': state}))
                self.assertIn('toolchain check made in this run', problem)


class PrepCache(unittest.TestCase):
    def test_use_cache_false_ignores_the_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / 'repo/tools/verifier').mkdir(parents=True)
            (tmp / 'bin').mkdir()
            (tmp / 'bin/cl.exe').write_bytes(b'compiler')
            (tmp / 'repo/tools/verifier/pinned.sha256').write_text(f'{sha(tmp / "bin/cl.exe")}  cl.exe\n')
            (tmp / 'image').write_bytes(b'image')
            wrapper = {'BINDIR': str(tmp / 'bin')}
            args = (tmp / 'repo', tmp, tmp / 'image', wrapper, sha(tmp / 'image'))
            with mock.patch.object(ub, 'boot_id', return_value='boot-1'):
                self.assertEqual(ub.prepare_host(*args, marker_dir=tmp)[0], 'checked')
                self.assertEqual(ub.prepare_host(*args, marker_dir=tmp)[0], 'cached')
                (tmp / 'bin/cl.exe').write_bytes(b'another compiler')
                # The cached path would trust the marker; a record-writing run must not.
                self.assertEqual(ub.prepare_host(*args, marker_dir=tmp)[0], 'cached')
                with self.assertRaises(ub.UnitError) as cm:
                    ub.prepare_host(*args, marker_dir=tmp, use_cache=False)
                self.assertEqual(cm.exception.code, ub.EXIT_TOOLCHAIN)


class HostAgentRefusal(unittest.TestCase):
    def test_bad_inputs_exit_with_the_agent_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, '-I', str(runners.AGENT), 'clean', '--run', str(Path(tmp) / 'Bad Name')],
                                  capture_output=True, text=True)
        self.assertEqual(proc.returncode, 45)
        self.assertIn('agent-error bad run directory name', proc.stdout)


class FakeAgentHost:
    """runners.AgentHost for confirm_runners: writes passing reports and the facts given."""
    made = []
    facts_by_host = {}

    def __init__(self, h, task, log=None, fresh_prep=False):
        self.h, self.task, self.fresh_prep = h, task, fresh_prep
        self.facts = None
        FakeAgentHost.made.append(self)

    def run(self, files, stage):
        return 0, ''

    def fetch(self, dest):
        for fn in self.task['functions']:
            d = Path(dest) / f'0x{fn["rva"]:x}'
            d.mkdir(parents=True, exist_ok=True)
            (d / 'report.json').write_text('{}')
        self.facts = FakeAgentHost.facts_by_host[self.h['host_id']]
        return Path(dest)


class ConfirmRunnersRun(unittest.TestCase):
    """confirm_runners.run: when records may go into reports/, and what reaches write_records."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.task = {'task_id': 'unit-a', 'dir': self.tmp / 'task', 'compiled': 'reconstruction/x/A.cpp',
                     'recipe': 'reconstruction/recipes/msvc-19.16.27054-o2.json', 'build_id': 'b',
                     'symbols_repo': 'reports/b/symbols.json',
                     'functions': [{'rva': 0x1000, 'size': 16, 'symbol': '?f@@YAXXZ'}]}
        self.task['dir'].mkdir()
        self.source = self.tmp / 'A.cpp'
        self.source.write_text('int a;\n')
        self.base = mock.Mock()
        self.base.source_state.return_value = ('base', [])
        self.base.result_of.return_value = ('pass', None)
        self.base.mac_compare.side_effect = lambda task, fn, host_dir, dest: (None, Path(dest) / 'report.json')
        self.base.build_block.return_value = {}
        self.base.notes.return_value = ['first', 'independence: fork', 'last']
        self.base.source_note.return_value = 'source'
        self.base.compare_steps.return_value = 'COMPARE'
        FakeAgentHost.made = []
        FakeAgentHost.facts_by_host = {
            'mac-wine': {'os': 'macos', 'machine': 'arm64', 'loader': 'wine', 'toolchain_check': 'checked',
                         'compiler_sha256': {'cl.exe': 'aa'}},
            'winpc-native': {'os': 'windows', 'machine': 'amd64', 'loader': 'native', 'toolchain_check': 'checked',
                             'compiler_sha256': {'cl.exe': 'aa'}}}
        self.written = []
        patches = [
            mock.patch.object(confirm_runners.confirm_session, 'prepare', side_effect=lambda base, d, replace, out: (
                self.task, {'reconstruction/x/A.cpp': self.source}, ['reconstruction/x/A.cpp'])),
            mock.patch.dict(os.environ, {'SR_VERIFIER_STATE': str(self.tmp / 'state')}),
            mock.patch.object(confirm_runners.confirm_session, 'write_records', side_effect=self.write_records),
            mock.patch.object(confirm_runners.runners, 'AgentHost', FakeAgentHost),
            mock.patch.object(confirm_runners.pipeline, 'lock', return_value=mock.Mock()),
            mock.patch.object(confirm_runners.pipeline, 'load_config', return_value={}),
            mock.patch.object(confirm_runners.subprocess, 'run',
                              return_value=subprocess.CompletedProcess([], 0, 'check: PASS\n', '')),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write_records(self, base, task, closure, recipe, runs, build_path, out, notes=None, reproduction=None):
        self.written.append({'out': out, 'runs': runs, 'notes': notes, 'reproduction': reproduction})
        for fn in task['functions']:
            path = confirm_runners.confirm_session.record_path(task, fn, out)
            if out is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({'runs': len(runs[fn['rva']])}))
        return ['  record written'], False

    def run_confirm(self, hosts, out=None, allowed=True, **kw):
        lines = []
        with mock.patch.object(confirm_runners, 'RUNNER_RECORDS_ALLOWED', allowed):
            code = confirm_runners.run(self.base, ['task'], out=out, log=lines.append, hosts=hosts, **kw)
        return code, lines

    def test_flag_false_refuses_reports_without_out(self):
        with self.assertRaises(pipeline.PipelineError) as cm:
            self.run_confirm([host(), ssh_host()], allowed=False)
        self.assertIn('--out', str(cm.exception))
        self.assertEqual((FakeAgentHost.made, self.written), ([], []))

    def test_flag_false_still_writes_inspection_records_with_out(self):
        code, _ = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', allowed=False)
        self.assertEqual(code, 0)
        self.assertEqual([w['out'] for w in self.written], [self.tmp / 'out'])

    def test_flag_true_writes_records_into_reports(self):
        code, lines = self.run_confirm([host(), ssh_host()])
        self.assertEqual(code, 0, lines)
        self.assertEqual(len(self.written), 1)
        w = self.written[0]
        self.assertIsNone(w['out'])
        # Own compares on both hosts plus the local cross-compare of the Windows object.
        self.assertEqual(sorted((a, b) for a, b, _ in w['runs'][0x1000]),
                         [('mac-wine', 'mac-wine'), ('winpc-native', 'mac-wine'), ('winpc-native', 'winpc-native')])
        self.assertTrue(w['notes'][1].startswith('independence: separate-machine, different-loader'))
        self.assertTrue(all(h.fresh_prep for h in FakeAgentHost.made))

    def test_reports_need_a_local_host(self):
        remote = ssh_host(host_id='winpc-wine', machine='other-pc', loader='wine')
        with self.assertRaises(pipeline.PipelineError) as cm:
            self.run_confirm([remote, ssh_host()])
        self.assertIn('local host', str(cm.exception))
        self.assertEqual((FakeAgentHost.made, self.written), ([], []))
        # Inspection records under --out are still possible without one.
        FakeAgentHost.facts_by_host['winpc-wine'] = dict(FakeAgentHost.facts_by_host['mac-wine'], os='linux')
        code, _ = self.run_confirm([remote, ssh_host()], out=self.tmp / 'out')
        self.assertEqual(code, 0)

    def test_reported_facts_that_fail_the_rule_write_nothing(self):
        cases = {'cached toolchain': ('winpc-native', {'toolchain_check': 'cached'}),
                 'native not on windows': ('winpc-native', {'os': 'macos'}),
                 'wrong loader': ('mac-wine', {'loader': 'native'})}
        for name, (hid, change) in cases.items():
            with self.subTest(name):
                saved = dict(FakeAgentHost.facts_by_host[hid])
                FakeAgentHost.facts_by_host[hid] = dict(saved, **change)
                try:
                    code, lines = self.run_confirm([host(), ssh_host()])
                finally:
                    FakeAgentHost.facts_by_host[hid] = saved
                self.assertEqual(code, 1)
                self.assertEqual(self.written, [])
                self.assertTrue(any('not independent' in line for line in lines), lines)

    def test_reproduction_names_both_loaders(self):
        self.run_confirm([host(), ssh_host()])
        recipe = json.loads((ROOT / self.task['recipe']).read_text())
        text = self.written[0]['reproduction'](self.task, self.task['functions'][0], ['reconstruction/x/A.cpp'], recipe)
        self.assertIn('<msvc>/bin/x64/cl ', text)
        self.assertIn('bin/Hostx64/x64/cl.exe', text)
        self.assertIn('INCLUDE', text)
        self.assertTrue(text.endswith('COMPARE'))

    # ---- journal and --resume

    def probe_with(self, **toolchain):
        def probe(h):
            found = toolchain.get(h['host_id'].replace('-', '_'), {'cl.exe': 'aa'})
            return {'toolchain': 'ok' if found else 'bad', 'image': 'ok', 'compiler_sha256': found or {}}
        return probe

    def first_run(self):
        code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out')
        self.assertEqual(code, 0, lines)
        self.assertEqual(len(self.written), 1)
        FakeAgentHost.made = []
        self.written = []

    def test_log_and_journal_are_written_as_each_unit_finishes(self):
        self.first_run()
        state = self.tmp / 'state'
        logs = list((state / 'confirm-logs').iterdir())
        self.assertEqual(len(logs), 1)
        self.assertIn('unit-a (reconstruction/x/A.cpp): records written', logs[0].read_text())
        journal = list((state / 'confirm-journal').iterdir())
        entries = [json.loads(line) for line in journal[0].read_text().splitlines()]
        self.assertEqual([e['task_id'] for e in entries], ['unit-a', 'unit-a'])
        self.assertEqual(entries[0]['records'], {})
        self.assertEqual(entries[1]['compiler_sha256'], {'mac-wine': {'cl.exe': 'aa'}, 'winpc-native': {'cl.exe': 'aa'}})

    def test_resume_skips_a_unit_complete_for_the_same_inputs_and_toolchains(self):
        self.first_run()
        code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', resume=True,
                                       probe_fn=self.probe_with())
        self.assertEqual(code, 0, lines)
        self.assertEqual((FakeAgentHost.made, self.written), ([], []))
        self.assertTrue(any('skipped' in line and 'unit-a' in line for line in lines), lines)

    def test_resume_reruns_when_a_toolchain_changed_between_runs(self):
        self.first_run()
        code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', resume=True, replace=True,
                                       probe_fn=self.probe_with(winpc_native={'cl.exe': 'bb'}))
        self.assertEqual(code, 0, lines)
        self.assertEqual(len(self.written), 1)
        self.assertTrue(all(h.fresh_prep for h in FakeAgentHost.made))

    def test_resume_reruns_when_a_host_check_fails_now(self):
        self.first_run()
        code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', resume=True, replace=True,
                                       probe_fn=self.probe_with(mac_wine=None))
        self.assertEqual(len(self.written), 1, lines)

    def test_resume_never_reuses_a_result_whose_inputs_differ(self):
        self.first_run()
        self.source.write_text('int b;\n')
        code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', resume=True, replace=True,
                                       probe_fn=self.probe_with())
        self.assertEqual(len(self.written), 1, lines)
        self.assertTrue(any('resume: 0 unit(s)' in line for line in lines), lines)

    def test_resume_reruns_when_a_record_changed_on_disk(self):
        self.first_run()
        record = self.tmp / 'out' / 'b' / '0x1000.json'
        record.write_text('{"edited": true}')
        self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', resume=True, replace=True, probe_fn=self.probe_with())
        self.assertEqual(len(self.written), 1)

    def test_resume_without_replace_keeps_records_it_would_rewrite(self):
        self.first_run()
        self.source.write_text('int c;\n')
        with self.assertRaises(pipeline.PipelineError) as cm:
            self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', resume=True, probe_fn=self.probe_with())
        self.assertIn('--replace', str(cm.exception))
        self.assertEqual(self.written, [])

    def test_host_refusal_writes_no_record_and_leaves_tombstone(self):
        with mock.patch.object(FakeAgentHost, 'run', return_value=(44, '')):
            code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out')
        self.assertEqual(code, 1)
        self.assertEqual(self.written, [])
        self.assertTrue(any('exit 44' in line for line in lines), lines)
        entry = confirm_runners.Journal(self.tmp / 'out').entries()['unit-a']
        self.assertEqual(entry['records'], {})

    def test_failed_replacement_invalidates_previous_success(self):
        self.first_run()
        with mock.patch.object(FakeAgentHost, 'run', return_value=(44, '')):
            code, _ = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', replace=True)
        self.assertEqual(code, 1)
        FakeAgentHost.made = []
        code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', replace=True, resume=True,
                                       probe_fn=self.probe_with())
        self.assertEqual(code, 0, lines)
        self.assertEqual(len(FakeAgentHost.made), 2)
        self.assertEqual(len(self.written), 1)

    def test_corrupt_or_unterminated_journal_entry_discards_earlier_successes(self):
        self.first_run()
        journal = confirm_runners.Journal(self.tmp / 'out')
        good = journal.path.read_bytes()
        for tail in (b'{"task_id": "unit', b'not json\n', b'\xff\n', b'null\n',
                     b'{"task_id": []}\n', good.splitlines()[-1]):
            with self.subTest(tail=tail):
                journal.path.write_bytes(good + tail)
                self.assertEqual(journal.entries(), {})
                journal.add({'task_id': 'unit-b', 'records': {}})
                self.assertEqual(journal.entries(), {'unit-b': {'task_id': 'unit-b', 'records': {}}})

    def test_torn_scheduling_append_cannot_hide_failed_replacement(self):
        self.first_run()
        journal = confirm_runners.Journal(self.tmp / 'out')
        with journal.path.open('ab') as f:
            f.write(b'{"records": {}, "task_id": "unit')
        with mock.patch.object(FakeAgentHost, 'run', return_value=(44, '')):
            code, _ = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', replace=True)
        self.assertEqual(code, 1)
        self.assertEqual(journal.entries()['unit-a']['records'], {})
        FakeAgentHost.made = []
        code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', replace=True, resume=True,
                                       probe_fn=self.probe_with())
        self.assertEqual(code, 0, lines)
        self.assertEqual(len(FakeAgentHost.made), 2)
        self.assertEqual(len(self.written), 1)

    def test_finisher_exception_reports_its_cause(self):
        with mock.patch.object(self.base, 'build_block', side_effect=OSError('missing build input')):
            code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out')
        self.assertEqual(code, 1)
        self.assertTrue(any('finisher OSError: missing build input' in line for line in lines), lines)
        self.assertFalse(any('not every host returned' in line for line in lines), lines)

    def test_resume_reruns_when_mac_comparison_image_changes(self):
        image = self.tmp / 'image'
        image.write_bytes(b'first')
        with mock.patch.object(pipeline, 'load_config', return_value={'image': str(image)}):
            self.first_run()
            image.write_bytes(b'second')
            code, lines = self.run_confirm([host(), ssh_host()], out=self.tmp / 'out', replace=True, resume=True,
                                           probe_fn=self.probe_with())
        self.assertEqual(code, 0, lines)
        self.assertEqual(len(self.written), 1)

    def test_batched_host_gives_the_same_runs_and_facts_check(self):
        batches = []

        class FakeBatchHost:
            def __init__(self, h, log=None, fresh_prep=False):
                self.h, self.fresh_prep = h, fresh_prep

            def run(self, units, stage, dests):
                batches.append(([t['task_id'] for t, _ in units], self.fresh_prep))
                out = {}
                for task, _ in units:
                    dest = Path(dests[task['task_id']])
                    for fn in task['functions']:
                        (dest / f'0x{fn["rva"]:x}').mkdir(parents=True, exist_ok=True)
                    out[task['task_id']] = (0, dest, FakeAgentHost.facts_by_host[self.h['host_id']])
                return out

        with mock.patch.object(confirm_runners.runners, 'BatchHost', FakeBatchHost):
            code, lines = self.run_confirm([host(), ssh_host(batch=8)])
            self.assertEqual(code, 0, lines)
            self.assertEqual(batches, [(['unit-a'], True)])
            self.assertEqual(sorted((a, b) for a, b, _ in self.written[0]['runs'][0x1000]),
                             [('mac-wine', 'mac-wine'), ('winpc-native', 'mac-wine'),
                              ('winpc-native', 'winpc-native')])
            # A batch whose host reports a cached toolchain check still writes nothing.
            self.written = []
            FakeAgentHost.facts_by_host['winpc-native'] = dict(FakeAgentHost.facts_by_host['winpc-native'],
                                                               toolchain_check='cached')
            code, lines = self.run_confirm([host(), ssh_host(batch=8)])
            self.assertEqual((code, self.written), (1, []))


class Slots(unittest.TestCase):
    def test_second_holder_waits_and_busy_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            order = []
            with runners.slot('h', 1, directory=tmp, poll=0.01) as waited:
                self.assertLess(waited, 1)
                self.assertEqual(runners.slots_busy('h', 1, directory=tmp), 1)

                def second():
                    with runners.slot('h', 1, directory=tmp, poll=0.01) as w:
                        order.append(('second', w))
                t = threading.Thread(target=second)
                t.start()
                time.sleep(0.2)
                order.append(('first-done', None))
            t.join(5)
            self.assertEqual([o[0] for o in order], ['first-done', 'second'])
            self.assertGreater(order[1][1], 0.1)
            self.assertEqual(runners.slots_busy('h', 1, directory=tmp), 0)

    def test_several_slots_take_only_free_ones_beyond_the_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            with runners.slots('h', 4, 8, directory=tmp, poll=0.01) as held:
                self.assertEqual(held, 4)
                self.assertEqual(runners.slots_busy('h', 4, directory=tmp), 4)
            with runners.slot('h', 4, directory=tmp), runners.slot('h', 4, directory=tmp):
                with runners.slots('h', 4, 4, directory=tmp, poll=0.01) as held:
                    self.assertEqual(held, 2)
            self.assertEqual(runners.slots_busy('h', 4, directory=tmp), 0)

    def test_parallel_limit_and_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            with runners.slot('h', 2, directory=tmp), runners.slot('h', 2, directory=tmp):
                self.assertEqual(runners.slots_busy('h', 2, directory=tmp), 2)
                with self.assertRaises(runners.RunnerError):
                    with runners.slot('h', 2, wait=0.05, directory=tmp, poll=0.01):
                        pass


class StubSsh(runners.LocalTransport):
    """Runs the host side here, but checks every command line like SshTransport and records it."""

    def __init__(self, h):
        super().__init__(h)
        self.commands = []

    def run(self, argv, timeout):
        for token in argv:
            if not runners.SAFE_TOKEN.fullmatch(token):
                raise AssertionError(f'unsafe token on an ssh command line: {token!r}')
        self.commands.append(list(argv))
        return super().run(argv, timeout)

    def join(self, *parts):
        return '/'.join(p.rstrip('/') for p in parts)


class AgentEndToEnd(unittest.TestCase):
    """attempt's host interface (run, fetch) through host_agent.py and unit_build.py."""

    MARKER = 'int candidate_source_marker_7f3a;'

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir='/tmp' if Path('/tmp').is_dir() else None)).resolve()
        src, self.msvc, self.log = self.tmp / 'src', self.tmp / 'msvc', self.tmp / 'log'
        self.log.mkdir()
        inputs = sp.inputs()
        self.image = self.tmp / 'image.pe'
        self.image.write_bytes(inputs['image_bytes'])
        self.object = self.tmp / 'synthetic.obj'
        self.object.write_bytes(inputs['object_bytes'])
        bindir = self.msvc / 'bin/x64'
        bindir.mkdir(parents=True)
        (bindir / 'cl.exe').write_bytes(b'fake compiler binary')
        base = 'z:' + str(self.msvc).replace('/', '\\')
        (bindir / 'msvcenv.sh').write_text(f"BASE='{base}'\nBINDIR='{bindir}'\n"
                                           f"export INCLUDE='{base}\\vc\\include'\n")
        (bindir / 'cl').write_text(FAKE_CL)
        (bindir / 'cl').chmod(0o755)
        files = {}
        for name in ('tools/compare.py', 'tools/pecoff.py', 'tools/source_digest.py',
                     'tools/verifier/verify_function.py', 'tools/verifier/unit_build.py'):
            files[name] = ROOT / name
        pins = src / 'tools/verifier/pinned.sha256'
        pins.parent.mkdir(parents=True)
        pins.write_text(f'{sha(bindir / "cl.exe")}  cl.exe\n')
        files['tools/verifier/pinned.sha256'] = pins
        written = {'builds/target.json': json.dumps(inputs['manifest']),
                   'reconstruction/synth/Synth.h': f'#pragma once\nint SyntheticSum(int* p);\n{self.MARKER}\n',
                   'reconstruction/synth/Synth.cpp': '#include "Synth.h"\n',
                   'task/symbols.json': json.dumps(inputs['symbol_map'])}
        for name, text in written.items():
            (src / name).parent.mkdir(parents=True, exist_ok=True)
            (src / name).write_text(text)
            files[name] = src / name
        (src / 'reconstruction/recipes').mkdir(parents=True)
        (src / 'reconstruction/recipes/r.json').write_bytes(sp.recipe())
        files['reconstruction/recipes/r.json'] = src / 'reconstruction/recipes/r.json'
        self.files = files
        t = inputs['task']
        self.task = {'task_id': 'synthetic', 'build_id': 'synthetic-fixture', 'compiled': 'reconstruction/synth/Synth.cpp',
                     'recipe': 'reconstruction/recipes/r.json', 'symbols_repo': None,
                     'functions': [{'rva': t['rva'], 'size': t['size'], 'symbol': t['symbol']}]}
        self.rva = t['rva']
        self.env = mock.patch.dict(os.environ, {'FAKE_MODE': 'ok', 'FAKE_LOG': str(self.log),
                                                'FAKE_OBJECT': str(self.object), 'FAKE_TOOLCHAIN': str(self.msvc),
                                                'SR_VERIFIER_STATE': str(self.tmp / 'state')})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp)

    def make(self, backend):
        h = host(msvc=str(self.msvc), work=str(self.tmp / 'work'), image=str(self.image), wine_bin=None,
                 wineprefix=None, max_parallel=1)
        if backend == 'ssh':
            h = dict(h, backend='ssh', python=[sys.executable])
            transport = StubSsh(h)
        else:
            transport = runners.LocalTransport(h)
        return runners.AgentHost(h, self.task, transport=transport), transport

    def run_one(self, backend):
        worker, transport = self.make(backend)
        code, out = worker.run(self.files, self.tmp / 'stage')
        dest = worker.fetch(self.tmp / f'dest-{backend}')
        return code, out, dest, worker, transport

    def test_local_pass_records_host_facts_and_cleans_up(self):
        code, out, dest, worker, _ = self.run_one('local')
        self.assertEqual(code, 0, out)
        report = json.loads((dest / f'0x{self.rva:x}' / 'report.json').read_text())
        self.assertEqual((report['result'], report['reason']), ('pass', 'all-checks-passed'))
        facts = json.loads((dest / 'result.json').read_text())['host_facts']
        self.assertEqual(facts['loader'], 'wine')
        self.assertEqual(facts['compiler_sha256'], {'cl.exe': sha(self.msvc / 'bin/x64/cl.exe')})
        self.assertEqual(worker.facts, facts)
        self.assertNotIn(str(self.tmp), out)
        self.assertEqual([p.name for p in (self.tmp / 'work').iterdir() if p.name != '.prep'], [])
        self.assertEqual(list((self.tmp / 'stage').iterdir()), [])

    def test_ssh_stub_sends_only_plain_tokens_and_no_source(self):
        code, out, dest, worker, transport = self.run_one('ssh')
        self.assertEqual(code, 0, out)
        self.assertTrue((dest / 'candidate.obj').is_file())
        commands = [' '.join(c) for c in transport.commands]
        self.assertTrue(any(' run ' in c for c in commands) and any(c.endswith(' clean --run ' + c.split('--run ')[-1])
                                                                     for c in commands))
        for c in commands:
            self.assertNotIn(self.MARKER, c)
            self.assertNotIn('SyntheticSum', c)
        # The agent runs isolated (-I), so a module left in the work directory cannot shadow a standard one.
        for argv in transport.commands:
            if argv[0] == sys.executable:
                self.assertEqual(argv[1], '-I')
        self.assertEqual([p.name for p in (self.tmp / 'work').iterdir() if p.name != '.prep'], [])

    def test_compile_failure_is_fetched_and_counted_by_exit_code(self):
        with mock.patch.dict(os.environ, {'FAKE_MODE': 'fail'}):
            code, out, dest, _, _ = self.run_one('local')
        self.assertEqual(code, 3)
        self.assertIn('undeclared', (dest / 'compile.log').read_text())
        self.assertNotIn('undeclared', out)

    def test_wrong_toolchain_is_refused_on_the_host(self):
        (self.msvc / 'bin/x64/cl.exe').write_bytes(b'another compiler')
        worker, _ = self.make('local')
        code, out = worker.run(self.files, self.tmp / 'stage')
        self.assertEqual(code, ub.EXIT_TOOLCHAIN)
        dest = worker.fetch(self.tmp / 'dest')
        self.assertEqual(json.loads((dest / 'error.json').read_text())['status'], 'toolchain-mismatch')

    def test_fresh_prep_hashes_the_toolchain_every_run(self):
        worker, _ = self.make('local')
        worker.run(self.files, self.tmp / 'stage')
        worker.fetch(self.tmp / 'd1')
        if ub.boot_id() is not None:
            worker.run(self.files, self.tmp / 'stage')
            worker.fetch(self.tmp / 'd2')
            self.assertEqual(worker.facts['toolchain_check'], 'cached')
        fresh, _ = self.make('local')
        fresh.fresh_prep = True
        code, _ = fresh.run(self.files, self.tmp / 'stage')
        self.assertEqual(code, 0)
        fresh.fetch(self.tmp / 'd3')
        self.assertEqual(fresh.facts['toolchain_check'], 'checked')

    def batch(self, ids=('unit-a', 'unit-b')):
        h = dict(host(msvc=str(self.msvc), work=str(self.tmp / 'work'), image=str(self.image), wine_bin=None,
                      wineprefix=None, max_parallel=2), backend='ssh', python=[sys.executable])
        transport = StubSsh(h)
        worker = runners.BatchHost(h, transport=transport, fresh_prep=True)
        alternative = self.tmp / 'other.cpp'
        alternative.write_text('#include "Synth.h"\n// distinct unit\n')
        units = [(dict(self.task, task_id=tid), dict(self.files, **({'reconstruction/synth/Synth.cpp': alternative}
                  if i else {}))) for i, tid in enumerate(ids)]
        results = worker.run(units, self.tmp / 'stage', {tid: self.tmp / 'dest' / tid for tid in ids})
        return results, transport

    def test_batch_runs_each_unit_with_its_own_fresh_check(self):
        results, transport = self.batch()
        self.assertEqual(sorted(results), ['unit-a', 'unit-b'])
        digests = {}
        for tid, (code, dest, facts) in results.items():
            self.assertEqual(code, 0, tid)
            source = self.files['reconstruction/synth/Synth.cpp'] if tid == 'unit-a' else self.tmp / 'other.cpp'
            names = ['reconstruction/synth/Synth.cpp', 'reconstruction/synth/Synth.h']
            import hashlib
            digests[tid] = hashlib.sha256(''.join(f'{sha(source if n.endswith(".cpp") else self.files[n])}  {n}\n'
                                                    for n in sorted(names)).encode()).hexdigest()
            result = json.loads((dest / 'result.json').read_text())
            self.assertEqual(result['source_revision'], digests[tid])
            report = json.loads((dest / f'0x{self.rva:x}' / 'report.json').read_text())
            self.assertEqual(report['result'], 'pass')
            self.assertEqual(report['source']['source_revision'], digests[tid])
            self.assertEqual(facts['toolchain_check'], 'checked')
            self.assertEqual(facts['compiler_sha256'], {'cl.exe': sha(self.msvc / 'bin/x64/cl.exe')})
            self.assertTrue((dest / 'candidate.obj').is_file())
        self.assertNotEqual(digests['unit-a'], digests['unit-b'])
        # One agent command for the batch and one clean; nothing but plain tokens, no source.
        self.assertEqual([c[c.index('-I') + 2] for c in transport.commands], ['batch', 'clean'])
        for c in transport.commands:
            self.assertNotIn(self.MARKER, ' '.join(c))
        self.assertEqual([p.name for p in (self.tmp / 'work').iterdir() if p.name != '.prep'], [])
        self.assertEqual(list((self.tmp / 'stage').iterdir()), [])

    def test_batch_missing_one_agent_result_affects_only_that_unit(self):
        unpack = runners.unpack

        def omit_one(archive, dest):
            unpack(archive, dest)
            (Path(dest) / 'unit-b.agent.json').unlink()

        with mock.patch.object(runners, 'unpack', side_effect=omit_one):
            results, _ = self.batch()
        self.assertIsInstance(results['unit-b'], runners.RunnerError)
        code, dest, _ = results['unit-a']
        self.assertEqual(code, 0)
        report = json.loads((dest / f'0x{self.rva:x}' / 'report.json').read_text())
        self.assertEqual(report['result'], 'pass')
        expected = source_digest.tu_digest(self.tmp / 'src', ['reconstruction/synth/Synth.cpp',
                                                              'reconstruction/synth/Synth.h'])
        self.assertEqual(report['source']['source_revision'], expected)

    def test_batch_rejects_agent_json_suffix(self):
        with self.assertRaisesRegex(runners.RunnerError, 'ends in'):
            self.batch(('unit-a', 'unit-a.agent.json'))

    def test_batch_refuses_a_changed_toolchain_per_unit(self):
        (self.msvc / 'bin/x64/cl.exe').write_bytes(b'another compiler')
        results, _ = self.batch()
        for tid, (code, dest, facts) in results.items():
            self.assertEqual(code, ub.EXIT_TOOLCHAIN, tid)
            self.assertEqual(json.loads((dest / 'error.json').read_text())['status'], 'toolchain-mismatch')
            self.assertIsNone(facts)

    def test_batch_agent_refuses_unsafe_unit_names(self):
        work = self.tmp / 'work'
        work.mkdir()
        name = 'batch-0123456789ab'
        runners.make_bundle(work, name, {}, {'units.json': json.dumps(['../escape']).encode()})
        proc = subprocess.run([sys.executable, '-I', str(work / f'{name}.py'), 'batch', '--run', str(work / name),
                               '--bundle', str(work / f'{name}.tar'), '--msvc', str(self.msvc), '--image',
                               str(self.image), '--loader', 'wine', '--label', 'mac-wine', '--jobs', '2'],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 45, proc.stdout + proc.stderr)
        self.assertIn('bad unit list', proc.stdout)

    def test_probe(self):
        h = host(msvc=str(self.tmp / 'nomsvc'), work=str(self.tmp / 'work'), image=str(self.image))
        with mock.patch.object(runners, 'REPO', self.tmp / 'src'):
            p = runners.probe(h, transport=StubSsh(dict(h, backend='ssh', python=[sys.executable])))
        self.assertEqual(p['toolchain'], 'missing')
        self.assertEqual(p['image'], 'ok')
        self.assertEqual(p['loader'], 'wine')
        self.assertEqual([x.name for x in (self.tmp / 'work').iterdir() if x.name != '.prep'], [])


class LoaderPaths(unittest.TestCase):
    def test_native_settings_mirror_the_wrapper_include_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'VC/Tools/MSVC/14.16.27023/bin/Hostx64/x64').mkdir(parents=True)
            (root / 'Windows Kits/10/Include/10.0.19041.0').mkdir(parents=True)
            s = ub.native_settings(root)
            parts = s['INCLUDE'].split(';')
            self.assertEqual(len(parts), 7)
            self.assertTrue(parts[0].endswith('14.16.27023\\atlmfc\\include'))
            self.assertTrue(parts[3].endswith('10.0.19041.0\\ucrt'))
            self.assertIsNone(ub.include_problem(s['INCLUDE'], s['BASE']))
            (root / 'Windows Kits/10/Include/10.0.22000.0').mkdir()
            with self.assertRaises(ub.UnitError):
                ub.native_settings(root)

    def test_classify_windows_paths(self):
        repo, tool, out = ub.classify_includes_windows(
            ['C:\\sr\\work\\r\\repo\\reconstruction\\a\\B.h', 'c:\\SR\\msvc\\VC\\include\\cstdint',
             'C:\\sr\\work\\r\\repo\\..\\evil.h', 'C:\\Windows\\x.h', 'C:\\sr\\work\\r\\repository\\x.h'],
            'C:/sr/work/r/repo', 'C:\\sr\\msvc')
        self.assertEqual(repo, ['reconstruction/a/B.h'])
        self.assertEqual(tool, 1)
        self.assertEqual(len(out), 3)

    def test_fold_case_accepts_only_closure_files(self):
        closure = ['reconstruction/a/B.cpp', 'reconstruction/a/B.h']
        files, rest = ub.fold_case_includes(['/w/repo/reconstruction/a/b.h', '/w/repo/reconstruction/a/c.h',
                                             '/usr/include/x.h'], '/w/repo', closure, [])
        self.assertEqual(files, ['reconstruction/a/B.h'])
        self.assertEqual(rest, ['/w/repo/reconstruction/a/c.h', '/usr/include/x.h'])


if __name__ == '__main__':
    unittest.main()
