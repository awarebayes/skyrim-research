"""Execute the POSIX launcher against synthetic Python installations, without host discovery."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == 'nt', 'POSIX launcher')
class SrTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'checkout with spaces'
        self.install = Path(self.tmp.name) / 'install'
        (self.root / 'tools').mkdir(parents=True)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.home = self.root / 'home'
        self.home.mkdir()
        self.env = {'PATH': str(self.bin), 'HOME': str(self.home)}
        # Relocate system install roots in the fixture so a real Homebrew Python cannot mask
        # the missing-interpreter case. The executable wrapper otherwise runs as shipped.
        self.text = (ROOT / 'sr').read_text()
        for prefix in ('/opt/homebrew', '/usr/local', '/Library/Frameworks'):
            self.text = self.text.replace(prefix, str(self.install / prefix.lstrip('/')))
        self.launcher = self.root / 'sr'
        self.launcher.write_text(self.text)
        self.launcher.chmod(0o755)
        os.symlink(shutil.which('dirname'), self.bin / 'dirname')
        self.command('uname', 'printf "%s\\n" Darwin')
        (self.root / 'tools/contrib.py').write_text(
            'import json, os, sys\n'
            'print(json.dumps({"args": sys.argv[1:], "launcher": os.environ["SR_LAUNCHER"], '
            '"utf8": os.environ["PYTHONUTF8"], "selected": os.environ["SR_TEST_SELECTED"]}))\n'
            'sys.exit(23)\n')

    def tearDown(self):
        self.tmp.cleanup()

    def command(self, name, body, directory=None):
        path = (directory or self.bin) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)
        return path

    def python(self, name, directory=None, valid=True):
        if valid:
            body = f'export SR_TEST_SELECTED={shlex.quote(name)}\nexec {shlex.quote(sys.executable)} "$@"'
        else:
            body = 'exit 1'  # Version or pyexpat probe failed.
        return self.command(name, body, directory)

    def run_sr(self, *args):
        return subprocess.run([str(self.launcher), *args], env=self.env, cwd=self.home,
                              capture_output=True, text=True)

    def test_prefers_versioned_python_and_preserves_args_and_exit_code(self):
        self.python('python3.13')
        self.python('python3')
        proc = self.run_sr('--json', 'start', 'argument with spaces', 'literal;$value')
        self.assertEqual(proc.returncode, 23, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data['args'], ['--json', 'start', 'argument with spaces', 'literal;$value'])
        self.assertEqual((data['selected'], data['launcher'], data['utf8']), ('python3.13', './sr', '1'))

    def test_skips_a_failed_probe(self):
        self.python('python3.13', valid=False)
        self.python('python3.12')
        proc = self.run_sr('doctor')
        self.assertEqual(proc.returncode, 23, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['selected'], 'python3.12')

    def test_probe_checks_both_version_and_pyexpat(self):
        # Record the actual probe, rather than merely asserting text in the wrapper.
        probe = self.root / 'probe.txt'
        self.command('python3.13', f'printf "%s" "$2" > {shlex.quote(str(probe))}\nexit 1')
        self.run_sr('doctor')
        self.assertIn('pyexpat', probe.read_text())
        self.assertIn('sys.version_info < (3, 11)', probe.read_text())

    def test_finds_homebrew_pyenv_and_uv_without_path_entries(self):
        roots = [self.install / 'opt/homebrew/opt/python@3.13/bin',
                 self.home / '.pyenv/versions/3.13.9/bin',
                 self.home / '.local/share/uv/python/cpython-3.13.9-test/bin']
        for directory in roots:
            with self.subTest(directory=directory):
                candidate = self.python('python3.13', directory=directory)
                proc = self.run_sr('doctor')
                self.assertEqual(proc.returncode, 23, proc.stderr)
                candidate.unlink()

    def test_generic_python_is_a_checked_fallback(self):
        self.python('python3')
        proc = self.run_sr('doctor')
        self.assertEqual(proc.returncode, 23, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['selected'], 'python3')

    def test_missing_python_prints_platform_install_commands(self):
        for platform, manager, command in (
                ('Darwin', None, 'brew install python@3.13'),
                ('Linux', 'apt-get', 'sudo apt update && sudo apt install python3'),
                ('Linux', 'dnf', 'sudo dnf install python3')):
            with self.subTest(platform=platform, manager=manager):
                self.command('uname', f'printf "%s\\n" {platform}')
                if manager:
                    self.command(manager, 'exit 0')
                proc = self.run_sr('doctor')
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(command, proc.stderr.splitlines())
                if manager:
                    (self.bin / manager).unlink()


if __name__ == '__main__':
    unittest.main()
