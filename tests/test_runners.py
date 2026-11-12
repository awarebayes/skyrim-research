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

    def test_rejections(self):
        cases = [
            (dict(runners_schema=2), 'runners_schema'),
            (dict(hosts={}), 'at least one host'),
            (dict(hosts={'mac': host(host_id='Mac/Path')}), 'host_id'),
            (dict(hosts={'mac': host(), 'winpc': ssh_host(host_id='mac-wine')}), 'used twice'),
            (dict(hosts={'mac': host(machine=None)}), 'machine'),
            (dict(hosts={'mac': host(loader='rosetta')}), 'loader'),
            (dict(hosts={'mac': host(max_parallel=0)}), 'max_parallel'),
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
