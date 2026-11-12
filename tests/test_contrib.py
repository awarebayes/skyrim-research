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
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import contrib  # noqa: E402
import lint_reconstruction  # noqa: E402
import synthetic_pecoff as sp  # noqa: E402

STUB = json.dumps([sys.executable, str(ROOT / 'tests' / 'stub_cl.py')])
TARGET = json.loads((ROOT / 'builds/target.json').read_text())
# A function still open for claims; the inventory changes as functions are accepted.
MAPPED = next(f['rva'] for f in json.loads((ROOT / 'data/progress.json').read_text())['functions']
              if f['status'] == 'mapped' and contrib.PLAIN_NAME.fullmatch(f.get('name') or ''))


class FakeGitHub:
    def __init__(self, items=None, me='me', offline=False, can_create=True, after_create=None):
        self.items, self.me, self.offline, self.can_create = items or {}, me, offline, can_create
        self.repo, self.created, self.comments, self.closed = contrib.UPSTREAM, [], [], []
        self.after_create = after_create

    def open_items(self, refresh=False):
        if self.offline:
            raise contrib.Offline('no network in tests')
        if refresh and self.created and self.after_create is not None:
            return self.after_create
        return self.items

    def close(self, number, body):
        self.closed.append(number)
        return True

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
    return {'number': number, 'title': f'claim: x 0x{MAPPED:x} A::B', 'url': f'https://github.com/x/y/issues/{number}',
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
            code = contrib.main(['--json', 'claim', f'0x{MAPPED:x}', *extra], ctx=ctx)
        return code, json.loads(out.getvalue())

    def test_json_shape(self):
        code, out = self.run_claim(FakeGitHub())
        self.assertEqual(code, 0)
        for key in ('command', 'ok', 'exit_code', 'error', 'next', 'messages'):
            self.assertIn(key, out)
        self.assertEqual(out['claim'], 'https://github.com/x/y/issues/99')

    def test_collision_is_refused(self):
        gh = FakeGitHub({MAPPED: [item('someone', 1)]})
        code, out = self.run_claim(gh)
        self.assertEqual(code, contrib.CLAIMED)
        self.assertEqual(gh.created, [])
        self.assertIn('someone', out['error'])

    def test_lapsed_claim_needs_take_over(self):
        gh = FakeGitHub({MAPPED: [item('someone', contrib.CLAIM_DAYS + 1, 7)]})
        self.assertEqual(self.run_claim(gh)[0], contrib.CLAIMED)
        code, _ = self.run_claim(gh, '--take-over')
        self.assertEqual(code, 0)
        self.assertEqual(gh.comments, [7])

    def test_own_claim_is_reused(self):
        gh = FakeGitHub({MAPPED: [item('me', 30)]})
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

    def test_unit_files_are_written_with_lf(self):
        path = self.tmp / 'u.cpp'
        contrib.write_source(path, 'a\nb\n')
        self.assertEqual(path.read_bytes(), b'a\nb\n')

    def test_candidates_prefer_new_units_and_small_sizes(self):
        rows = contrib.candidates(ROOT, contrib.inventory(ROOT))
        startable = [r for r in rows if r['startable']]
        self.assertTrue(startable)
        firsts = [r for r in startable if not r['unit_exists']]
        self.assertEqual(startable[:len(firsts)], firsts)
        self.assertEqual([r['size'] for r in firsts], sorted(r['size'] for r in firsts))


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

    def test_out_of_scope_and_oversized_files(self):
        (self.repo / 'tools').mkdir()
        (self.repo / 'tools/x.py').write_text('print(1)\n')
        (self.repo / 'reconstruction/forms/Big.h').write_text('//' + 'x' * contrib.MAX_UNIT_FILE_BYTES)
        self.commit()
        problems = contrib.intake_problems(self.ctx(repo=self.repo), 'HEAD~1', 'HEAD')
        text = '\n'.join(problems)
        self.assertIn('tools/x.py: outside contributor scope', text)
        self.assertIn('contributor cap', text)

    def test_sibling_material_is_allowed_on_the_drafters_terms(self):
        cpp = self.repo / 'reconstruction/forms/TESActorBaseData.cpp'
        cpp.write_text(cpp.read_text().replace(
            '// Labels: v2', '// Labels: v2\n// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/a.cpp:1'))
        self.commit()
        self.assertEqual(contrib.intake_problems(self.ctx(repo=self.repo), 'HEAD~1', 'HEAD'), [])
        # Another repository or revision is still refused by the lint.
        cpp.write_text(cpp.read_text().replace('fnv_decomp@91e1b6e8', 'fnv_decomp@0123abcd'))
        self.commit()
        self.assertTrue(contrib.intake_problems(self.ctx(repo=self.repo), 'HEAD~1', 'HEAD'))

    def test_intake_reads_the_named_head_not_the_working_tree(self):
        self.commit()
        self.git('switch', '-q', '-c', 'crafted')
        (self.repo / 'tools').mkdir()
        (self.repo / 'tools/x.py').write_text('print(1)\n')
        self.commit()
        self.git('switch', '-q', '-')
        problems = contrib.intake_problems(self.ctx(repo=self.repo), 'HEAD~1', 'crafted')
        self.assertTrue(any('tools/x.py' in p for p in problems))
        self.assertFalse((self.repo / 'tools/x.py').exists())


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


class SubmitTests(Base):
    """submit's blockers, the sanitized PR body and commit message, and a dry run that writes no git state."""

    RVA = 0x1de5e0
    SECRETS = ('SECRET-DETAIL-TEXT', '+0x9', 'SECRET-BIND-LINE', '/private/abs/dir')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, check=True, capture_output=True, text=True).stdout

    def setUp(self):
        super().setUp()
        self.repo = self.tmp / 'repo'
        for rel in ('builds/target.json', contrib.DEFAULT_RECIPE, 'findings/fifth-batch-selection.md',
                    '.github/PULL_REQUEST_TEMPLATE/function.md'):
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.repo / rel)
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'base')
        fn = next(f for f in contrib.inventory(ROOT)['functions'] if f['rva'] == self.RVA)
        h, cpp = contrib.skeleton(fn, 'TESActorBaseData', 'Unk_07', 'forms', 'tester', contrib.DEFAULT_RECIPE)
        self.unit = ['reconstruction/forms/TESActorBaseData.h', 'reconstruction/forms/TESActorBaseData.cpp']
        (self.repo / 'reconstruction/forms').mkdir(parents=True)
        (self.repo / self.unit[0]).write_text(h)
        (self.repo / self.unit[1]).write_text(cpp)
        self.tdir = self.private / 'tasks' / 'contrib-tesactorbasedata'
        self.tdir.mkdir(parents=True)
        self.task = {'task_id': self.tdir.name, 'build_id': TARGET['build_id'], 'compiled': self.unit[1],
                     'recipe': contrib.DEFAULT_RECIPE, 'symbols': 'symbols.json',
                     'functions': [{'rva': f'0x{self.RVA:x}', 'size': fn['size'], 'symbol': 'x',
                                    'community_name': fn['name']}],
                     'contrib': {'practice': False, 'unit': self.unit}}
        from source_digest import include_closure, tu_digest
        digest = tu_digest(self.repo, include_closure(self.repo, self.unit[1]))
        self.summary = {
            'task': self.tdir.name, 'run': 1, 'unit': self.unit[1], 'source_revision': digest,
            'recipe': contrib.DEFAULT_RECIPE, 'recipe_sha256': 'ab' * 32, 'compiler': 'pinned',
            'image_sha256_pinned': True, 'comparator': {'version': 'x'}, 'contract_version': 2, 'practice': False,
            'functions': [{'rva': f'0x{self.RVA:x}', 'name': fn['name'], 'result': 'pass', 'reason': 'all-checks-passed',
                           'detail': self.SECRETS[0], 'hint': 'h', 'first_mismatch': self.SECRETS[1],
                           'candidate_size': 3, 'target_size': 3, 'coverage': {'code_bytes_total': 3},
                           'code_section_sha256': 'cd' * 32}],
            'bind': [self.SECRETS[2]], 'private_dir': self.SECRETS[3]}
        self.write()

    def write(self):
        (self.tdir / 'task.json').write_text(json.dumps(self.task))
        (self.tdir / 'last-compare.json').write_text(json.dumps(self.summary))

    def runner(self, cmd, **kw):
        # The repository-wide check is not under test here; everything else really runs.
        if any(str(c).endswith('tools/check.py') for c in cmd):
            return subprocess.CompletedProcess(cmd, 0, '', '')
        return subprocess.run(cmd, **kw)

    def submit(self, gh=None, *extra):
        ctx = self.ctx(repo=self.repo, github=gh or FakeGitHub(), runner=self.runner,
                       env={'PATH': '/usr/bin:/bin', 'HOME': str(self.tmp)})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = contrib.main(['--json', 'submit', '--dry-run', '--base', 'HEAD', *extra], ctx=ctx)
        return code, json.loads(out.getvalue())

    def state(self):
        return (self.git('rev-parse', 'HEAD'), self.git('status', '--porcelain'), self.git('diff', '--cached'),
                self.git('branch', '--list'))

    def test_dry_run_is_clean_and_writes_no_git_state(self):
        before = self.state()
        code, out = self.submit()
        self.assertEqual((code, out['blockers']), (0, []), out)
        self.assertEqual(self.state(), before)
        body = (self.tdir / 'pr-body.md').read_text()
        message_plan = ' '.join(out['plan'])
        for text in (body, out['title']):
            for secret in self.SECRETS:
                self.assertNotIn(secret, text)
            self.assertNotIn(str(self.tmp), text)
            self.assertNotIn(str(self.private), text)
            self.assertNotIn('packs/', text)
            self.assertNotIn(str(Path.home()), text)
        self.assertIn(f'-- {" ".join(self.unit)}', message_plan)

    def test_commit_message_is_sanitized(self):
        # The message a real submit commits with is the one the dry run reports.
        code, out = self.submit()
        self.assertEqual(code, 0)
        message = out['commit_message']
        self.assertTrue(message.startswith(out['title']))
        for secret in self.SECRETS:
            self.assertNotIn(secret, message)
        self.assertNotIn(str(self.tmp), message)

    def blockers(self, gh=None):
        code, out = self.submit(gh)
        self.assertEqual(code, contrib.FAILED)
        return '\n'.join(out['blockers'])

    def test_stand_in_compiler_blocks(self):
        self.summary['compiler'] = 'override'
        self.write()
        self.assertIn('stand-in compiler', self.blockers())

    def test_changed_unit_blocks(self):
        (self.repo / self.unit[1]).write_text((self.repo / self.unit[1]).read_text() + '\n')
        self.assertIn('changed since the last compare', self.blockers())

    def test_failed_function_blocks(self):
        self.summary['functions'][0]['result'] = 'fail'
        self.write()
        self.assertIn('not every function passed', self.blockers())

    def test_practice_task_blocks(self):
        self.task['contrib']['practice'] = True
        self.write()
        self.assertIn('practice tasks', self.blockers())

    def test_undeclared_adapted_body_blocks(self):
        import check_origin
        hit = {'trivial': False, 'fork_of': None, 'declared': False}
        with unittest.mock.patch.object(check_origin, 'check_unit', return_value=[hit]), \
                unittest.mock.patch.object(check_origin, 'describe', return_value='close to a community body'):
            self.assertIn('not declared in the unit header', self.blockers())

    def test_fresh_foreign_claim_blocks_on_any_function(self):
        self.task['functions'].append({'rva': '0xf2120', 'size': 3, 'symbol': 'y', 'community_name': 'A::B'})
        self.write()
        gh = FakeGitHub({0xf2120: [item('someone', 1, 5)]})
        self.assertIn('0xf2120', self.blockers(gh))
        code, out = self.submit(gh, '--ack-collision')
        self.assertEqual(out['blockers'], [])

    def test_other_staged_files_stop_a_real_submit(self):
        (self.repo / 'notes.txt').write_text('x\n')
        self.git('add', 'notes.txt')
        ctx = self.ctx(repo=self.repo, github=FakeGitHub(), runner=self.runner,
                       env={'PATH': '/usr/bin:/bin', 'HOME': str(self.tmp)})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = contrib.main(['--json', 'submit', '--base', 'HEAD'], ctx=ctx)
        self.assertEqual(code, contrib.USAGE)
        self.assertIn('notes.txt', json.loads(out.getvalue())['error'])
        self.assertEqual(self.git('log', '--oneline').count('\n'), 1)


class ClaimFollowUpTests(Base):
    def claim(self, gh, *extra, env=None):
        ctx = self.ctx(github=gh, env=env or {'PATH': ''})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = contrib.main(['--json', 'claim', f'0x{MAPPED:x}', *extra], ctx=ctx)
        return code, json.loads(out.getvalue())

    def test_link_only_is_not_recorded_as_claimed(self):
        code, out = self.claim(FakeGitHub(can_create=False))
        self.assertEqual((code, out['claim']), (0, 'link-only'))
        self.assertNotIn(f'0x{MAPPED:x}', contrib.local_claims(self.ctx()))

    def test_older_rival_after_creating_withdraws_ours(self):
        rival = item('someone', 0, 98)
        mine = dict(item('me', 0, 99), url='https://github.com/x/y/issues/99')
        gh = FakeGitHub(after_create={MAPPED: [rival, mine]})
        code, out = self.claim(gh)
        self.assertEqual(code, contrib.CLAIMED)
        self.assertEqual(gh.closed, [99])
        self.assertNotIn(f'0x{MAPPED:x}', contrib.local_claims(self.ctx()))

    def test_unknown_login_with_open_items_asks_for_it(self):
        gh = FakeGitHub({MAPPED: [item('someone', 1)]}, me=None)
        code, out = self.claim(gh)
        self.assertEqual(code, contrib.USAGE)
        self.assertIn('--github-user', out['next'])

    def test_paging_goes_past_five_hundred(self):
        pages = [[{'number': i, 'title': f'claim: x 0x{0x100000 + i:x} A::B', 'html_url': f'u/{i}',
                   'user': {'login': 'a'}, 'updated_at': '2026-01-01T00:00:00Z'} for i in range(p * 100, p * 100 + 100)]
                 for p in range(6)] + [[]]
        gh = contrib.GitHub(self.ctx(env={'PATH': ''}))
        gh.api = lambda path: pages[int(path.rsplit('page=', 1)[1]) - 1]
        self.assertEqual(len(gh.open_items()), 600)


class FollowUpTests(Base):
    def test_winget_source_agreements_need_their_own_flag(self):
        ctx = self.ctx()
        plain = contrib.install_command(ctx, 'winget', [['LLVM.LLVM']])[0]
        self.assertNotIn('--accept-source-agreements', plain)
        self.assertIn('--accept-source-agreements', contrib.install_command(ctx, 'winget', [['LLVM.LLVM']], True)[0])
        args = contrib.parser().parse_args(['--yes', 'setup'])
        self.assertFalse(args.accept_winget_source_agreements)

    def test_steamcmd_depot_route_and_its_download_folder(self):
        lines = '\n'.join(contrib.steamcmd_route(self.ctx()))
        self.assertIn(f'download_depot {contrib.STEAM_APP_ID} {contrib.STEAM_EXE_DEPOT} {contrib.STEAM_EXE_MANIFEST}',
                      lines)
        home = self.tmp / 'home'
        exe = (home / 'Library/Application Support/Steam/steamapps/content' / f'app_{contrib.STEAM_APP_ID}'
               / f'depot_{contrib.STEAM_EXE_DEPOT}' / 'SkyrimSE.exe')
        ctx = self.ctx(platform='darwin', env={'HOME': str(home)})
        found = contrib.exe_candidates(ctx, exists=lambda p: p == str(exe), dir_exists=lambda p: False)
        self.assertEqual(found, [str(exe)])

    def test_apt_steamcmd_is_left_to_the_person(self):
        bin_dir = self.tmp / 'bin'
        bin_dir.mkdir()
        for tool in ('git', 'apt-get', 'wine', 'msiextract', 'llvm-objdump'):
            (bin_dir / tool).write_text('#!/bin/sh\nexit 0\n')
            (bin_dir / tool).chmod(0o755)
        ran = []
        ctx = self.ctx(env={'PATH': str(bin_dir), 'HOME': str(self.tmp), 'SR_MSVC': str(self.tmp / 'msvc'),
                            'SR_SKYRIM_EXE': str(self.tmp / 'none.exe')},
                       platform='linux', assume_yes=True, runner=lambda cmd, **kw: ran.append(cmd))
        with self.assertRaises(contrib.Stop) as cm:
            contrib.cmd_setup(ctx, contrib.parser().parse_args(['setup', '--steamcmd']))
        steps = {s['step']: s for s in cm.exception.data['steps']}
        self.assertEqual(steps['steamcmd']['status'], 'needs-person')
        self.assertIn('sudo apt install steamcmd', steps['steamcmd']['detail'])
        self.assertFalse(any('steamcmd' in ' '.join(map(str, c)) for c in ran))

    def test_area_must_be_a_plain_directory_name(self):
        ctx = self.ctx(env={'PATH': ''})
        for bad in ('../tools', 'Forms', 'a/b', ''):
            args = contrib.parser().parse_args(['start', f'0x{MAPPED:x}', '--area', bad])
            with self.assertRaises(contrib.Stop) as cm:
                contrib.start(ctx, args)
            self.assertEqual(cm.exception.code, contrib.USAGE, bad)
            self.assertIn('--area must be', cm.exception.message)

    def test_redact_hides_checkout_and_home(self):
        home = str(self.tmp / 'home')
        ctx = self.ctx(repo=self.tmp / 'home/src/skyrim-research', env={'HOME': home})
        ctx.redact = True
        text = ctx.scrub(f'{self.tmp}/home/src/skyrim-research/.local/x and {home}/Games/SkyrimSE.exe')
        self.assertEqual(text, '<repo>/.local/x and ~/Games/SkyrimSE.exe')

    def test_practice_tasks_have_their_own_id_and_are_not_picked_by_default(self):
        self.assertEqual(contrib.task_id_for('NiNode', practice=True), 'practice-ninode')
        for tid, practice in (('practice-ninode', True), ('contrib-ninode', False)):
            d = self.private / 'tasks' / tid
            d.mkdir(parents=True)
            (d / 'task.json').write_text(json.dumps({'compiled': 'x', 'functions': [],
                                                     'contrib': {'practice': practice}}))
        self.assertEqual(contrib.load_task(self.ctx())[0].name, 'contrib-ninode')

    def test_self_test_is_skipped_not_passed_without_its_function(self):
        repo = self.tmp / 'repo'
        (repo / 'data').mkdir(parents=True)
        (repo / 'data/progress.json').write_text(json.dumps({'functions': []}))
        code, data, _ = contrib.run_self_test(self.ctx(repo=repo))
        self.assertTrue(data['skipped'])
        self.assertEqual(data['functions'], [])

    def test_no_licence_link_means_no_acceptance(self):
        vsman = self.tmp / 'VisualStudio.vsman'
        vsman.write_text(json.dumps({'packages': []}))
        self.assertIsNone(contrib.licence_url(vsman))

    def test_case_folded_include_is_matched_only_to_closure_files(self):
        root = '/Users/A/repo'
        repo_files = []
        with unittest.mock.patch.object(contrib, 'same_file', return_value=True):
            rest = contrib.fold_case_includes(['/users/a/repo/reconstruction/forms/X.h'.lower(),
                                               'Z:/users/a/repo/reconstruction/forms/../../secret.h',
                                               '/users/a/elsewhere/X.h'], root, ['reconstruction/forms/X.h'],
                                              repo_files)
        self.assertEqual(repo_files, ['reconstruction/forms/X.h'])
        self.assertEqual(len(rest), 2)

    def test_case_folded_include_must_open_the_closure_file_itself(self):
        root = self.tmp / 'repo'
        (root / 'reconstruction/forms').mkdir(parents=True)
        (root / 'reconstruction/forms/X.h').write_text('// closure file\n')
        other = self.tmp / 'other'
        other.mkdir()
        (other / 'X.h').write_text('// another file\n')
        exact = str(root / 'reconstruction/forms/X.h')
        repo_files = []
        self.assertEqual(contrib.fold_case_includes([exact], root, ['reconstruction/forms/X.h'], repo_files), [])
        self.assertEqual(repo_files, ['reconstruction/forms/X.h'])
        # A name that folds to a closure entry but opens nothing, or another file, is still outside.
        missing = str(root / 'reconstruction/forms/Y.h')
        repo_files = []
        self.assertEqual(contrib.fold_case_includes([missing], root, ['reconstruction/forms/y.h'], repo_files),
                         [missing])
        self.assertEqual(repo_files, [])
        with unittest.mock.patch.object(contrib.os.path, 'samefile', return_value=False):
            self.assertEqual(contrib.fold_case_includes([exact], root, ['reconstruction/forms/X.h'], []), [exact])
        self.assertFalse(contrib.same_file(exact, other / 'X.h'))

    def test_manifest_hash_mismatch_stops_before_any_licence_or_download(self):
        pins = contrib.recipe_constants(ROOT)
        work = self.private / 'toolchain-work' / 'msvc-wine' / '.git'
        work.mkdir(parents=True)

        def runner(cmd, **kw):
            out = pins['MSVC_WINE_COMMIT'] if cmd[:2] == ['git', 'rev-parse'] else ''
            return subprocess.CompletedProcess(cmd, 0, out, '')

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        ctx = self.ctx(repo=ROOT, runner=runner, env={'PATH': ''})
        with unittest.mock.patch.object(contrib.urllib.request, 'urlopen', return_value=Resp(b'{"tampered": 1}')):
            with self.assertRaises(contrib.Stop) as cm:
                contrib.install_toolchain(ctx, accept=True)
        self.assertEqual(cm.exception.code, contrib.FAILED)
        self.assertIn('pinned SHA-256', cm.exception.message)
        self.assertFalse((self.private / 'toolchain-work' / 'VisualStudio.vsman').exists())

    def test_fetch_sources_pins_each_revision_and_reports_network_failure(self):
        ran = []

        def runner(cmd, **kw):
            ran.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, '', '')
        repo = self.tmp / 'repo'
        ctx = self.ctx(repo=repo, runner=runner)
        sources = {'a/b': ('.local/sources/b', 'f' * 40, 'MIT')}
        self.assertEqual(contrib.fetch_sources(ctx, sources), ['a/b'])
        self.assertIn(['git', 'fetch', '-q', '--depth', '1', 'https://github.com/a/b.git', 'f' * 40], ran)
        ctx.runner = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 128, '', 'no network')
        with self.assertRaises(contrib.Stop) as cm:
            contrib.fetch_sources(ctx, sources)
        self.assertEqual(cm.exception.code, contrib.NETWORK)

    def test_go_resumes_unsubmitted_work(self):
        d = self.private / 'tasks' / 'contrib-a'
        d.mkdir(parents=True)
        (d / 'task.json').write_text(json.dumps({'task_id': 'contrib-a', 'compiled': 'reconstruction/forms/A.cpp',
                                                 'contrib': {'practice': False, 'unit': ['x']}}))
        args = contrib.parser().parse_args(['go'])
        with unittest.mock.patch.object(contrib, 'cmd_setup', return_value=(0, {}, None)), \
                unittest.mock.patch.object(contrib, 'cmd_claim') as claim:
            code, data, nxt = contrib.cmd_go(self.ctx(), args)
        self.assertTrue(data['resumed'])
        claim.assert_not_called()

    def test_release_closes_only_own_claim_issues(self):
        gh = FakeGitHub({MAPPED: [item('me', 1, 3), item('someone', 1, 4),
                                    dict(item('me', 1, 5), pull_request=True)]})
        contrib.save_local_claim(self.ctx(), MAPPED, {'status': 'published', 'url': 'u'})
        code, data, _ = contrib.cmd_release(self.ctx(github=gh), contrib.parser().parse_args(['release', f'0x{MAPPED:x}']))
        self.assertEqual(gh.closed, [3])
        self.assertNotIn(f'0x{MAPPED:x}', contrib.local_claims(self.ctx()))

    def test_planner_skips_open_claims_and_warns_offline(self):
        sys.path.insert(0, str(ROOT / 'tools' / 'ghidra'))
        import export_pack
        gh = FakeGitHub({MAPPED: [item('someone', 1)], 0x2000: [item('someone', contrib.CLAIM_DAYS + 3)]})
        with unittest.mock.patch.object(contrib.Ctx, 'github', return_value=gh):
            self.assertEqual(export_pack.open_claim_rvas(), {MAPPED})
        err = io.StringIO()
        with unittest.mock.patch.object(contrib.Ctx, 'github', return_value=FakeGitHub(offline=True)), \
                contextlib.redirect_stderr(err):
            self.assertEqual(export_pack.open_claim_rvas(), set())
        self.assertIn('not checked', err.getvalue())


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
