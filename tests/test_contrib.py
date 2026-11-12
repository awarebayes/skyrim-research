"""Tests for tools/contrib.py, the contributor helper, with synthetic inputs only.

No game file, compiler or network is used: the executable is a synthetic PE image, the compiler is
tests/stub_cl.py, GitHub is a fake object, and Windows paths are exercised through the pure path
helpers on any host.
"""
import contextlib
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import contrib  # noqa: E402
import lint_reconstruction  # noqa: E402
import synthetic_pecoff as sp  # noqa: E402

STUB = json.dumps([sys.executable, str(ROOT / 'tests' / 'stub_cl.py')])
TARGET = json.loads((ROOT / 'builds/target.json').read_text())


class FakeGitHub:
    def __init__(self, items=None, me='me', offline=False, can_create=True):
        self.items, self.me, self.offline, self.can_create = items or {}, me, offline, can_create
        self.repo, self.created, self.comments = contrib.UPSTREAM, [], []

    def open_items(self):
        if self.offline:
            raise contrib.Offline('no network in tests')
        return self.items

    def user(self):
        return self.me

    def gh(self):
        return 'gh' if self.can_create else None

    def create_issue(self, title, body):
        if not self.can_create:
            return None
        self.created.append(title)
        return 'https://github.com/x/y/issues/99'

    def new_issue_link(self, title, body):
        return 'https://github.com/x/y/issues/new?title=' + title

    def comment(self, number, body):
        self.comments.append(number)
        return True


def item(author, days_ago, number=1):
    when = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat().replace('+00:00', 'Z')
    return {'number': number, 'title': 'claim: x 0x1de5e0 A::B', 'url': f'https://github.com/x/y/issues/{number}',
            'author': author, 'updated_at': when, 'pull_request': False}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.private = self.tmp / 'private'

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ctx(self, **kw):
        kw.setdefault('interactive', False)
        kw.setdefault('as_json', True)
        kw.setdefault('private', self.private)
        return contrib.Ctx(**kw)


class ExecutableTests(Base):
    def test_hash_and_version(self):
        blob = bytearray(b'MZ' + bytes(200))
        blob[64:68] = b'\xbd\x04\xef\xfe'
        blob[72:80] = (7 | 1 << 16).to_bytes(4, 'little') + (0 | 104 << 16).to_bytes(4, 'little')
        exe = self.tmp / 'SkyrimSE.exe'
        exe.write_bytes(bytes(blob))
        self.assertEqual(contrib.pe_version(exe), '1.7.104.0')
        target = dict(TARGET, image_sha256=contrib.sha256_file(exe))
        self.assertEqual(contrib.inspect_exe(exe, target)['status'], 'ok')

    def test_wrong_build_names_the_pinned_version_only(self):
        exe = self.tmp / 'SkyrimSE.exe'
        exe.write_bytes(b'MZ not the pinned image')
        info = contrib.inspect_exe(exe, TARGET)
        self.assertEqual(info['status'], 'wrong-build')
        text = contrib.wrong_build_message(info, TARGET)
        self.assertIn(TARGET['version'], text)
        self.assertIn(TARGET['image_sha256'][:16], text)
        for word in ('crack', 'patcher', 'downgrade', 'depot'):
            self.assertNotIn(word, text.lower())

    def test_missing_executable(self):
        self.assertEqual(contrib.inspect_exe(self.tmp / 'nope.exe', TARGET)['status'], 'missing')
        ctx = self.ctx(env={'PATH': '', 'HOME': str(self.tmp)})
        with self.assertRaises(contrib.Stop) as cm:
            contrib.require_exe(ctx, TARGET)
        self.assertEqual(cm.exception.code, contrib.MISSING)
        self.assertIn('setup --exe', cm.exception.next_action)

    def test_windows_steam_libraries(self):
        vdf = '"libraryfolders"\n{\n "1"\n {\n  "path"  "D:\\\\Games\\\\SteamLibrary"\n }\n}\n'
        dirs = {r'C:\Program Files (x86)\Steam'}
        files = {r'D:\Games\SteamLibrary\steamapps\common\Skyrim Special Edition\SkyrimSE.exe'}
        ctx = self.ctx(platform='win32', env={'ProgramFiles(x86)': r'C:\Program Files (x86)',
                                              'ProgramFiles': r'C:\Program Files', 'USERPROFILE': r'C:\Users\a'})
        found = contrib.exe_candidates(ctx, exists=lambda p: p in files, dir_exists=lambda p: p in dirs,
                                       read=lambda p: vdf)
        self.assertEqual(found, [r'D:\Games\SteamLibrary\steamapps\common\Skyrim Special Edition\SkyrimSE.exe'])
        self.assertEqual(ctx.cli, 'py tools\\contrib.py')

    def test_steamcmd_route_never_carries_credentials(self):
        lines = contrib.steamcmd_route(self.ctx())
        self.assertIn('login <your-steam-login>', lines)
        self.assertTrue(any(contrib.STEAM_APP_ID in line for line in lines))
        self.assertFalse(any('password' in line.lower() and '<' not in line and 'asks' not in line for line in lines))


class ToolchainTests(Base):
    def test_missing_compiler(self):
        ctx = self.ctx(env={'SR_MSVC': str(self.tmp / 'msvc'), 'PATH': ''})
        self.assertEqual(contrib.check_toolchain(ctx)['status'], 'missing')

    def test_mismatching_compiler(self):
        bin_dir = self.tmp / 'msvc/VC/Tools/MSVC/14.16.27023/bin/Hostx64/x64'
        bin_dir.mkdir(parents=True)
        for name in ('cl.exe', 'c1xx.dll', 'c2.dll', 'link.exe'):
            (bin_dir / name).write_bytes(b'not the pinned binary')
        state = contrib.check_toolchain(self.ctx(env={'SR_MSVC': str(self.tmp / 'msvc')}))
        self.assertEqual(state['status'], 'mismatch')
        self.assertEqual(sorted(state['differing']), ['c1xx.dll', 'c2.dll', 'cl.exe', 'link.exe'])

    def test_doctor_names_one_next_step(self):
        ctx = self.ctx(env={'SR_MSVC': str(self.tmp / 'msvc'), 'PATH': '/usr/bin:/bin', 'HOME': str(self.tmp),
                            'SR_SKYRIM_EXE': str(self.tmp / 'none.exe')}, platform='linux')
        code, data, nxt = contrib.cmd_doctor(ctx, type('A', (), {'exe': None})())
        self.assertEqual(code, contrib.MISSING)
        self.assertIn('setup --exe', nxt)
        self.assertTrue(all({'check', 'ok', 'required', 'detail', 'fix'} <= set(c) for c in data['checks']))

    def test_recipe_constants_come_from_the_verifier_recipe(self):
        pins = contrib.recipe_constants(ROOT)
        self.assertEqual(len(pins['VSMAN_SHA256']), 64)
        self.assertTrue(pins['VSMAN_URL'].startswith('https://download.visualstudio.microsoft.com/'))

    def test_classify_windows_paths(self):
        repo = r'C:\Users\a\skyrim-research'
        opened = [r'c:\users\a\skyrim-research\reconstruction\forms\A.h',
                  r'C:\tools\msvc\VC\Tools\MSVC\14.16.27023\include\cstdint',
                  r'C:\Program Files (x86)\Windows Kits\10\Include\10.0.19041.0\ucrt\stdio.h',
                  r'C:\Users\a\Desktop\secret.txt']
        files, tools, outside = contrib.classify_windows(opened, repo, [r'C:\tools\msvc',
                                                                         r'C:\Program Files (x86)\Windows Kits\10'])
        self.assertEqual(files, ['reconstruction/forms/A.h'])
        self.assertEqual(tools, 2)
        self.assertEqual(outside, [r'C:\Users\a\Desktop\secret.txt'])

    def test_install_needs_licence_without_terminal(self):
        ctx = self.ctx(env={'PATH': ''})
        with self.assertRaises(contrib.Stop) as cm:
            ctx.ask('Install wine?', '--yes')
        self.assertEqual(cm.exception.code, contrib.CONSENT)
        self.assertIn('--yes', cm.exception.next_action)
        self.assertTrue(self.ctx(assume_yes=True).ask('Install wine?', '--yes'))

    def test_setup_without_yes_does_not_install_when_not_a_terminal(self):
        bin_dir = self.tmp / 'bin'
        bin_dir.mkdir()
        for tool in ('git', 'apt-get'):
            (bin_dir / tool).write_text('#!/bin/sh\nexit 0\n')
            (bin_dir / tool).chmod(0o755)
        ran = []
        ctx = self.ctx(env={'PATH': str(bin_dir), 'HOME': str(self.tmp), 'SR_MSVC': str(self.tmp / 'msvc')},
                       platform='linux', runner=lambda cmd, **kw: ran.append(cmd))
        args = contrib.parser().parse_args(['setup'])
        with self.assertRaises(contrib.Stop) as cm:
            contrib.cmd_setup(ctx, args)
        self.assertEqual(cm.exception.code, contrib.CONSENT)
        self.assertEqual(ran, [])

    def test_install_commands(self):
        ctx = self.ctx(interactive=False)
        cmds = contrib.install_command(ctx, 'apt-get', [['wine', 'wine64'], ['msitools']])
        self.assertIn('-n', cmds[0])  # sudo never waits for a password without a terminal
        self.assertEqual(contrib.install_command(ctx, 'brew', [['msitools'], ['--cask', 'wine-stable']]),
                         [['brew', 'install', 'msitools'], ['brew', 'install', '--cask', 'wine-stable']])
        self.assertEqual(contrib.install_command(ctx, 'winget', [['LLVM.LLVM']])[0][-1], 'LLVM.LLVM')


class ClaimTests(Base):
    def run_claim(self, gh, *extra):
        ctx = self.ctx(github=gh)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = contrib.main(['--json', 'claim', '0x1de5e0', *extra], ctx=ctx)
        return code, json.loads(out.getvalue())

    def test_json_shape(self):
        code, out = self.run_claim(FakeGitHub())
        self.assertEqual(code, 0)
        for key in ('command', 'ok', 'exit_code', 'error', 'next', 'messages'):
            self.assertIn(key, out)
        self.assertEqual(out['claim'], 'https://github.com/x/y/issues/99')

    def test_collision_is_refused(self):
        gh = FakeGitHub({0x1de5e0: [item('someone', 1)]})
        code, out = self.run_claim(gh)
        self.assertEqual(code, contrib.CLAIMED)
        self.assertEqual(gh.created, [])
        self.assertIn('someone', out['error'])

    def test_lapsed_claim_needs_take_over(self):
        gh = FakeGitHub({0x1de5e0: [item('someone', contrib.CLAIM_DAYS + 1, 7)]})
        self.assertEqual(self.run_claim(gh)[0], contrib.CLAIMED)
        code, _ = self.run_claim(gh, '--take-over')
        self.assertEqual(code, 0)
        self.assertEqual(gh.comments, [7])

    def test_own_claim_is_reused(self):
        gh = FakeGitHub({0x1de5e0: [item('me', 30)]})
        code, out = self.run_claim(gh)
        self.assertEqual(code, 0)
        self.assertEqual(gh.created, [])

    def test_offline(self):
        code, out = self.run_claim(FakeGitHub(offline=True))
        self.assertEqual(code, contrib.NETWORK)
        code, out = self.run_claim(FakeGitHub(offline=True), '--offline-ok')
        self.assertEqual((code, out['claim']), (0, 'unpublished'))

    def test_without_gh_gives_a_link(self):
        code, out = self.run_claim(FakeGitHub(can_create=False))
        self.assertEqual(code, 0)
        self.assertIn('issues/new', out['link'])

    def test_matched_function_cannot_be_claimed(self):
        ctx = self.ctx(github=FakeGitHub())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(contrib.main(['--json', 'claim', f'0x{contrib.SELF_TEST_RVA:x}'], ctx=ctx), contrib.USAGE)


class SkeletonTests(Base):
    def test_skeleton_passes_the_lint(self):
        data = contrib.inventory(ROOT)
        fn = next(f for f in data['functions'] if f['status'] == 'mapped' and 'powerof3' in f['name_source']
                  and contrib.PLAIN_NAME.fullmatch(f['name']))
        cls, method = contrib.PLAIN_NAME.fullmatch(fn['name']).groups()
        h, cpp = contrib.skeleton(fn, cls, method, 'forms', 'tester, no AI', contrib.DEFAULT_RECIPE)
        root = self.tmp / 'repo'
        for rel in ('builds/target.json', contrib.DEFAULT_RECIPE, fn['evidence']):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, root / rel)
        unit = root / 'reconstruction' / 'forms'
        unit.mkdir(parents=True, exist_ok=True)
        (unit / f'{cls}.h').write_text(h)
        (unit / f'{cls}.cpp').write_text(cpp)
        for rel in (f'reconstruction/forms/{cls}.h', f'reconstruction/forms/{cls}.cpp'):
            self.assertEqual(lint_reconstruction.lint_file(root, rel, TARGET['build_id']), [])
        self.assertIn('GPL-3.0', h)
        self.assertIn(f'RVA 0x{fn["rva"]:x}', cpp)

    def test_candidates_prefer_new_units_and_small_sizes(self):
        rows = contrib.candidates(ROOT, contrib.inventory(ROOT))
        startable = [r for r in rows if r['startable']]
        self.assertTrue(startable)
        firsts = [r for r in startable if not r['unit_exists']]
        self.assertEqual(startable[:len(firsts)], firsts)
        self.assertEqual([r['size'] for r in firsts], sorted(r['size'] for r in firsts))


class LintIncludeNameTests(Base):
    def lint(self, line):
        root = Path(tempfile.mkdtemp(dir=self.tmp))
        (root / 'builds').mkdir(parents=True)
        shutil.copy(ROOT / 'builds/target.json', root / 'builds/target.json')
        (root / 'reconstruction/forms').mkdir(parents=True)
        (root / 'reconstruction/forms/A.h').write_text(
            f'// A (build {TARGET["build_id"]}). Source exposure: black-box. Name origin: GUESS.\n'
            f'#pragma once\n{line}\nclass A {{}};\n')
        return lint_reconstruction.lint_file(root, 'reconstruction/forms/A.h', TARGET['build_id'])

    def test_host_paths_are_refused(self):
        self.assertEqual(self.lint('#include <cstdint>'), [])
        for bad in ('#include <C:/Windows/win.ini>', '#include <Z:\\home\\x.h>', '#include <sub/../x.h>',
                    '#include <.hidden>'):
            self.assertTrue(any('plain relative path' in p for p in self.lint(bad)), bad)


class IntakeTests(Base):
    def git(self, *args):
        subprocess.run(['git', *args], cwd=self.repo, check=True, capture_output=True)

    def setUp(self):
        super().setUp()
        self.repo = self.tmp / 'repo'
        for rel in ('builds/target.json', contrib.DEFAULT_RECIPE, 'findings/fifth-batch-selection.md'):
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.repo / rel)
        self.git('init', '-q')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'empty')
        self.git('add', '.')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'base')
        fn = next(f for f in contrib.inventory(ROOT)['functions'] if f['rva'] == 0x1de5e0)
        h, cpp = contrib.skeleton(fn, 'TESActorBaseData', 'Unk_07', 'forms', 'tester', contrib.DEFAULT_RECIPE)
        (self.repo / 'reconstruction/forms').mkdir(parents=True)
        (self.repo / 'reconstruction/forms/TESActorBaseData.h').write_text(h)
        (self.repo / 'reconstruction/forms/TESActorBaseData.cpp').write_text(cpp)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'change')

    def test_clean_unit_passes(self):
        self.commit()
        self.assertEqual(contrib.intake_problems(self.ctx(repo=self.repo), 'HEAD~1', 'HEAD'), [])

    def test_out_of_scope_and_sibling_additions(self):
        (self.repo / 'tools').mkdir()
        (self.repo / 'tools/x.py').write_text('print(1)\n')
        cpp = self.repo / 'reconstruction/forms/TESActorBaseData.cpp'
        cpp.write_text(cpp.read_text().replace(
            '// Labels: v2', '// Labels: v2\n// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/a.cpp:1'))
        (self.repo / 'reconstruction/forms/Big.h').write_text('//' + 'x' * contrib.MAX_UNIT_FILE_BYTES)
        self.commit()
        problems = contrib.intake_problems(self.ctx(repo=self.repo), 'HEAD~1', 'HEAD')
        text = '\n'.join(problems)
        self.assertIn('tools/x.py: outside contributor scope', text)
        self.assertIn('Sibling source', text)
        self.assertIn('contributor cap', text)


class CompareTests(Base):
    """compile -> bind -> comparator on synthetic inputs, through the stub compiler."""

    def setUp(self):
        super().setUp()
        self.repo = self.tmp / 'repo'
        inputs = sp.inputs()
        self.image = self.tmp / 'image.pe'
        self.image.write_bytes(inputs['image_bytes'])
        files = {'builds/target.json': json.dumps(dict(inputs['manifest'], version='synthetic', store='none')),
                 'reports/synthetic-fixture/symbol-map.json': json.dumps(inputs['symbol_map']),
                 'reconstruction/recipes/synthetic.json': inputs['recipe_bytes'].decode(),
                 'reconstruction/forms/Synthetic.h': '#pragma once\n',
                 'reconstruction/forms/Synthetic.cpp': '#include "Synthetic.h"\n'}
        for rel, text in files.items():
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(text)
        tdir = self.private / 'tasks' / 'contrib-synthetic'
        tdir.mkdir(parents=True)
        (tdir / 'task.json').write_text(json.dumps({
            'task_id': 'contrib-synthetic', 'build_id': 'synthetic-fixture', 'compiled': 'reconstruction/forms/Synthetic.cpp',
            'recipe': 'reconstruction/recipes/synthetic.json', 'symbols': 'symbols.json',
            'functions': [{'rva': hex(sp.LAYOUT[sp.FUNCTION]), 'size': len(sp.CODE), 'symbol': sp.FUNCTION,
                           'community_name': sp.FUNCTION}],
            'contrib': {'practice': False, 'unit': ['reconstruction/forms/Synthetic.h', 'reconstruction/forms/Synthetic.cpp']}}))
        self.ctx_ = self.ctx(repo=self.repo, env={'SR_CONTRIB_COMPILER': STUB, 'SR_SKYRIM_EXE': str(self.image),
                                                  'PATH': '/usr/bin:/bin', 'SR_OBJDUMP': '/nonexistent'})

    def test_pass_and_sanitized_summary(self):
        code, data, nxt = contrib.run_compare(self.ctx_, 'contrib-synthetic')
        self.assertEqual(code, contrib.OK, data)
        self.assertEqual(data['functions'][0]['reason'], 'all-checks-passed')
        self.assertEqual(data['compiler'], 'override')
        self.assertIn('submit', nxt)
        text = json.dumps({k: v for k, v in data.items() if k != 'private_dir'})
        self.assertNotIn(sp.CODE.hex()[:16], text)

    def test_compile_failure(self):
        self.ctx_.env['SR_STUB_FAIL'] = '1'
        with self.assertRaises(contrib.Stop) as cm:
            contrib.run_compare(self.ctx_, 'contrib-synthetic')
        self.assertEqual(cm.exception.code, contrib.COMPILE)
        self.assertTrue(cm.exception.data['errors'])

    def test_include_outside_the_closure_is_refused(self):
        (self.repo / 'reconstruction/forms/Synthetic.cpp').write_text('#include "Synthetic.h"\n#include "Missing.h"\n')
        with self.assertRaises(contrib.Stop) as cm:
            contrib.run_compare(self.ctx_, 'contrib-synthetic')
        self.assertEqual(cm.exception.code, contrib.UNIT)

    def test_wrong_image_is_refused_before_compiling(self):
        self.image.write_bytes(b'MZ other build')
        with self.assertRaises(contrib.Stop) as cm:
            contrib.run_compare(self.ctx_, 'contrib-synthetic')
        self.assertEqual(cm.exception.code, contrib.MISSING)


class JoinPageTests(unittest.TestCase):
    def test_numbers_come_from_the_inventory(self):
        from build_site import render_join
        data = contrib.inventory(ROOT)
        page = render_join(data, 'synthetic-revision')
        matched = sum(f['status'] == 'matched' for f in data['functions'])
        self.assertIn(f'{matched} accepted', page)
        self.assertNotIn('%', page.split('<main>')[1].split('</main>')[0].replace('100%', ''))


class CommandLineTests(unittest.TestCase):
    def test_non_tty_json_never_prompts(self):
        proc = subprocess.run([sys.executable, str(ROOT / 'tools/contrib.py'), '--json', 'doctor'],
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120,
                              env={'PATH': '/usr/bin:/bin', 'HOME': tempfile.gettempdir(),
                                   'SR_SKYRIM_EXE': '/nonexistent/SkyrimSE.exe', 'SR_MSVC': '/nonexistent'})
        out = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, out['exit_code'])
        self.assertIn('next', out)

    def test_rva_parsing(self):
        self.assertEqual(contrib.parse_rva('0x1DE5E0'), 0x1de5e0)
        with self.assertRaises(contrib.Stop):
            contrib.parse_rva('sub_1de5e0')
        self.assertEqual(str(PureWindowsPath(r'C:\a') / 'b'), r'C:\a\b')


if __name__ == '__main__':
    unittest.main()
