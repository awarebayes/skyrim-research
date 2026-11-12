"""Windows-specific behaviour of the contributor path, checked on any host with synthetic inputs:
line endings of checked-out sources and written skeletons, the sr.cmd entry point, and the
resumable toolchain download. No game file, compiler or network is used."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import contrib  # noqa: E402

SR_CMD = ROOT / 'sr.cmd'


class LineEndingTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('git'), 'git is not installed')
    def test_sources_check_out_lf_and_batch_files_crlf(self):
        proc = subprocess.run(['git', 'check-attr', 'eol', '--', 'reconstruction/forms/X.cpp',
                               'reconstruction/forms/X.h', 'sr.cmd'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        eol = dict(re.findall(r'^(\S+): eol: (\S+)$', proc.stdout, re.M))
        self.assertEqual(eol, {'reconstruction/forms/X.cpp': 'lf', 'reconstruction/forms/X.h': 'lf',
                               'sr.cmd': 'crlf'})

    def test_skeleton_files_are_written_with_lf(self):
        calls = []

        def spy(self, data, encoding=None, errors=None, newline=None):
            calls.append(newline)
            return len(data)
        with unittest.mock.patch.object(Path, 'write_text', spy):
            contrib.write_source(Path('unused.cpp'), 'int a;\n')
        self.assertEqual(calls, ['\n'])


class SrCmdTests(unittest.TestCase):
    def setUp(self):
        self.raw = SR_CMD.read_bytes()
        self.text = self.raw.decode('ascii')

    def test_working_tree_copy_is_crlf_only(self):
        # The repository stores it LF; .gitattributes gives CRLF in every checkout, the form
        # cmd.exe needs. A bare LF in the checkout would mean the attribute is not applied.
        self.assertNotIn(b'\n', self.raw.replace(b'\r\n', b''))

    def test_private_python_is_pinned(self):
        url = re.search(r'set "SR_PKG_URL=(\S+)"', self.text).group(1)
        sha = re.search(r'set "SR_PKG_SHA256=([0-9a-f]+)"', self.text).group(1)
        self.assertTrue(url.startswith('https://www.nuget.org/api/v2/package/python/'))
        self.assertEqual(len(sha), 64)
        self.assertIn('certutil -hashfile', self.text)
        # The version in the URL, the file name and the message agree.
        version = url.rsplit('/', 1)[1]
        self.assertIn(f'python.{version}.nupkg', self.text)
        self.assertIn(f'Python {version}', self.text)

    def test_no_parenthesized_blocks(self):
        # A checkout path with ")" would end a block early, so the script uses labels only.
        for line in self.text.splitlines():
            code = line.strip()
            if code.lower().startswith(('rem', 'echo')):
                continue
            self.assertFalse(code.endswith('('), line)
            self.assertNotEqual(code, ')', line)

    def test_names_itself_in_next_steps(self):
        launcher = re.search(r'set "SR_LAUNCHER=([^"]+)"', self.text).group(1)
        ctx = contrib.Ctx(platform='win32', env={'SR_LAUNCHER': launcher}, as_json=True)
        self.assertEqual(ctx.cli, '.\\sr.cmd')
        self.assertEqual(contrib.Ctx(platform='win32', env={}, as_json=True).cli, 'py tools\\contrib.py')
        self.assertEqual(contrib.Ctx(platform='linux', env={'SR_LAUNCHER': launcher}, as_json=True).cli,
                         'python3 tools/contrib.py')

    def test_runs_contrib_with_all_arguments_and_exit_code(self):
        self.assertIn('"%SR_ROOT%tools\\contrib.py" %*', self.text)
        self.assertIn('exit /b %ERRORLEVEL%', self.text)
        self.assertIn('set "PYTHONUTF8=1"', self.text)


class ToolchainCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.private = self.tmp / 'private'

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def install(self, vsdownload_rc):
        manifest = json.dumps({'packages': [{'id': 'Microsoft.VisualStudio.Product.BuildTools', 'localizedResources': [
            {'language': 'en-us', 'license': 'https://example.invalid/licence'}]}]}).encode()
        pins = dict(contrib.recipe_constants(ROOT), VSMAN_SHA256=hashlib.sha256(manifest).hexdigest())
        work = self.private / 'toolchain-work'
        (work / 'msvc-wine' / '.git').mkdir(parents=True)
        (work / 'VisualStudio.vsman').write_bytes(manifest)
        ran = []

        def runner(cmd, **kw):
            ran.append(cmd)
            if cmd[:2] == ['git', 'rev-parse']:
                return subprocess.CompletedProcess(cmd, 0, pins['MSVC_WINE_COMMIT'], '')
            if any(str(c).endswith('vsdownload.py') for c in cmd):
                cache = Path(cmd[cmd.index('--cache') + 1])
                (cache / 'pkg').mkdir(parents=True)
                (cache / 'pkg' / 'payload.vsix').write_bytes(b'x')
                if vsdownload_rc == 0:
                    dest = Path(cmd[cmd.index('--dest') + 1])
                    (dest / 'VC/Tools/MSVC/14.16.27023/bin/Hostx64/x64').mkdir(parents=True)
                return subprocess.CompletedProcess(cmd, vsdownload_rc, '', '')
            return subprocess.CompletedProcess(cmd, 0, '', '')
        ctx = contrib.Ctx(repo=ROOT, platform='win32', env={'PATH': ''}, as_json=True, private=self.private,
                          runner=runner)
        with unittest.mock.patch.object(contrib, 'recipe_constants', return_value=pins):
            try:
                result = contrib.install_toolchain(ctx, accept=True)
            except contrib.Stop as exc:
                result = exc
        return ran, work / 'cache', result

    def test_interrupted_download_keeps_finished_payloads(self):
        ran, cache, result = self.install(vsdownload_rc=1)
        self.assertIsInstance(result, contrib.Stop)
        self.assertEqual(result.code, contrib.FAILED)
        self.assertIn('resumes', result.next_action)
        self.assertTrue((cache / 'pkg' / 'payload.vsix').is_file())
        vs = next(c for c in ran if any(str(x).endswith('vsdownload.py') for x in c))
        self.assertEqual(vs[vs.index('--cache') + 1], str(cache))

    def test_cache_is_removed_after_a_finished_install(self):
        _ran, cache, result = self.install(vsdownload_rc=0)
        self.assertNotIsInstance(result, contrib.Stop)
        self.assertFalse(cache.exists())


if __name__ == '__main__':
    unittest.main()
