"""Contributor autopilot using only original synthetic source, fake GitHub and fake verifiers."""
import copy
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools/verifier'))
import contrib_autopilot as ap
import contrib_screen as screen
import unit_build


GOOD = b'''// Original synthetic fixture; source https://example.org/types.
#pragma once
#include <cstdint>
class Synth { public: int value; };
'''


def pr(number=1, author='contributor', head='a' * 40, paths=('reconstruction/synth/Synth.cpp',)):
    return dict(number=number, author=dict(login=author), headRefOid=head, isDraft=False,
                baseRefName='main', files=[dict(path=p) for p in paths])


class Screen(unittest.TestCase):
    def test_ordinary_headers_and_programmer_cpp(self):
        self.assertEqual(screen.screen(GOOD, 'Synth.h'), [])
        self.assertEqual(screen.screen(b'#pragma pack(push, 8)\n#pragma warning(disable: 4100)\n'
                                       b'#define COUNT 4\nint values[COUNT];\n#pragma pack(pop)\n', 'Synth.h'), [])

    def test_malicious_pattern_corpus(self):
        corpus = [
            b'#include "/etc/passwd"', b'#include "../private.h"', b'#include <../../private.h>',
            b'#include "Z:\\private.h"', b'#include HEADER', b'#include_next <cstdint>',
            b'# /**/ include "private.h"', b'%:include "private.h"', b'??=include "private.h"',
            b'#import "plugin.dll"', b'#pragma comment(lib, "plugin")', b'#pragma message("leak")',
            b'#pragma include_alias("a", "b")', b'#pragma code_seg("evil")', b'#pragma once; evil',
            b'__asm { ret }', b'_asm nop', b'asm("nop")', b'__asm__ ("nop")',
            b'__declspec(allocate("evil")) int x;', b'__declspec /*x*/ ( allocate("evil")) int x;',
            b'__pragma(comment(lib,"evil"))', b'_Pragma("once")', b'#define JOIN(a,b) a ## b',
            b'#de\\\nfine ASM __as\\\nm', b'char *path = "/etc/passwd";',
            b'#define PATH "../outside"', b'char *p="C:private";', b'char *p="\\x2e\\x2e";',
            b'char *p="\\057etc";', b'#line 1 "/etc/passwd"', b'R"(hidden)"',
            b'// \x00', b'// \x1b[31m', b'// \x7f', b'\xff',
            '// \u202e hidden'.encode(), '// \u200b hidden'.encode(),
        ]
        for blob in corpus:
            with self.subTest(blob=blob):
                self.assertTrue(screen.screen(blob, 'Synth.cpp'))

    def test_line_size_and_template_caps(self):
        for blob, code in [(b'x' * (screen.MAX_BYTES + 1), 'file-size-cap'),
                           (b'\n' * (screen.MAX_LINES + 1), 'line-count-cap'),
                           (b'x' * (screen.MAX_LINE + 1), 'line-length-cap'),
                           (b'T<' * (screen.MAX_DEPTH + 1), 'template-or-expression-depth'),
                           (b'#if X\n' * (screen.MAX_DEPTH + 1), 'preprocessor-depth')]:
            with self.subTest(code=code):
                self.assertIn(code, screen.screen(blob, 'Synth.cpp'))

    def test_macro_depth_cycles_and_exponential_expansion(self):
        self.assertIn('macro-depth-or-cycle', screen.screen(b'#define A B\n#define B A\n', 'Synth.h'))
        nested = '\n'.join(f'#define M{i} M{i+1}' for i in range(screen.MAX_DEPTH + 2))
        self.assertIn('macro-depth-or-cycle', screen.screen(nested.encode(), 'Synth.h'))
        expansion = '#define M0 x\n' + '\n'.join(f'#define M{i} M{i-1} M{i-1}' for i in range(1, 20))
        self.assertIn('macro-expansion-cap', screen.screen(expansion.encode(), 'Synth.h'))
        many = '\n'.join(f'#define M{i} {i}' for i in range(screen.MAX_MACROS + 1))
        self.assertIn('macro-count-cap', screen.screen(many.encode(), 'Synth.h'))

    def test_include_roots_checked_transitively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unit = root / 'reconstruction/synth'
            unit.mkdir(parents=True)
            (unit / 'Synth.cpp').write_text('#include "Synth.h"\n')
            (unit / 'Synth.h').write_bytes(GOOD)
            self.assertEqual(screen.screen_tree(root, 'reconstruction/synth/Synth.cpp'), [])
            (unit / 'Synth.h').write_text('#include <host-secret.h>\n')
            self.assertIn('include-outside-roots', screen.screen_tree(root, 'reconstruction/synth/Synth.cpp'))
            other = root / 'tools'
            other.mkdir()
            (other / 'Tool.h').write_text('int secret;\n')
            (unit / 'Synth.h').write_text('#include "tools/Tool.h"\n')
            with self.assertRaises(ValueError):
                screen.screen_tree(root, 'reconstruction/synth/Synth.cpp')

    def test_allowed_community_headers_are_repository_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'reconstruction/synth').mkdir(parents=True)
            (root / 'reconstruction/community').mkdir()
            (root / 'reconstruction/synth/Synth.cpp').write_text('#include <community/Types.h>\n')
            (root / 'reconstruction/community/Types.h').write_text('struct Synth {};\n')
            self.assertEqual(screen.screen_tree(root, 'reconstruction/synth/Synth.cpp'), [])


class Selection(unittest.TestCase):
    def test_scope_is_exact(self):
        self.assertIsNone(ap.selection_problem(pr()['files']))
        for path in ('tools/contrib.py', '.github/workflows/check.yml', 'reconstruction/synth/a.cpp',
                     'reconstruction/synth/Synth.hpp', 'reconstruction/synth/../Synth.cpp',
                     'reconstruction/a/b/Synth.cpp', '/reconstruction/synth/Synth.cpp'):
            self.assertIsNotNone(ap.selection_problem([dict(path=path)]))
        self.assertIsNotNone(ap.selection_problem([]))

    def test_oldest_one_per_contributor_case_insensitive_and_drafts_wait(self):
        rows = [pr(4, 'Alice'), pr(3, 'Bob'), pr(2, 'alice'), dict(pr(1, 'Alice'), isDraft=True)]
        self.assertEqual([p['number'] for p in ap.select_prs(rows)], [2, 3])


class FakeRuntime:
    def __init__(self):
        self.calls, self.messages = [], []
        self.crash = None
        self.unsafe, self.reject, self.scope = False, False, False
        self.intake_errors = []
        self.confirmed = dict(passed=['0x1000', '0x2000'], failed=[])
        self.reviewed = dict(groups=['g1'], failed=[])

    def call(self, name, value):
        self.calls.append(name)
        if self.crash == name:
            raise OSError('simulated crash')
        return copy.deepcopy(value)

    def fetch(self, pr):
        return self.call('fetch', dict(tree='synthetic', base='b' * 40, files=pr['files'], diff='synthetic'))

    def intake(self, fetched):
        return self.call('intake', self.intake_errors)

    def functions(self, fetched):
        if self.reject:
            raise ap.Rejected('per-PR function cap exceeded')
        return self.call('functions', {'reconstruction/synth/Synth.cpp': [4096, 8192]})

    def ai_screen(self, fetched):
        return self.call('screen', dict(safe=not self.unsafe, reasons=['suspicious compiler construct']))

    def export(self, fetched, units):
        return self.call('export', ['synthetic-task'])

    def confirm(self, fetched, tasks, revision):
        return self.call('confirm', self.confirmed)

    def make_groups(self, fetched, confirmed):
        return self.call('groups', ['g1'])

    def reviews(self, fetched, groups, tasks, revision):
        return self.call('reviews', self.reviewed)

    def publish(self, fetched, reviewed, revision):
        revision['enqueued'] = True
        return self.call('publish', dict(commits=['c' * 40], accepted=['0x1000'], dropped=1))

    def finish(self, revision, published):
        self.call('finish', None)

    def feedback(self, revision, key, label, message, **kwargs):
        self.messages.append((key, label, message))


class ResumeAndLimits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.config = dict(ap.DEFAULTS, daily_compiles=3, daily_reviews=2)
        self.state = ap.State(self.directory, self.config, '2026-01-01')
        self.runtime = FakeRuntime()

    def reload(self):
        self.state = ap.State(self.directory, self.config, '2026-01-01')

    def test_full_synthetic_pipeline_and_idempotent_completion(self):
        result = ap.process(self.runtime, self.state, pr())
        self.assertTrue(result['done'])
        self.assertEqual(self.runtime.calls, ['fetch', 'intake', 'functions', 'screen', 'export',
                                             'confirm', 'groups', 'reviews', 'publish', 'finish'])
        self.reload()
        ap.process(self.runtime, self.state, pr())
        self.assertEqual(self.runtime.calls.count('fetch'), 1)
        self.assertEqual(self.runtime.calls.count('publish'), 1)

    def test_crash_at_every_stage_resumes_without_repeating_successes(self):
        stages = ['fetch', 'intake', 'functions', 'screen', 'export', 'confirm', 'groups', 'reviews', 'publish', 'finish']
        for stage in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                state = ap.State(Path(tmp), self.config)
                runtime = FakeRuntime()
                runtime.crash = stage
                with self.assertRaises(OSError):
                    ap.process(runtime, state, pr())
                before = list(runtime.calls)
                runtime.crash = None
                state = ap.State(Path(tmp), self.config)
                self.assertTrue(ap.process(runtime, state, pr())['done'])
                for success in before[:-1]:
                    self.assertEqual(runtime.calls.count(success), 1)

    def test_updated_head_does_not_inherit_successes(self):
        ap.process(self.runtime, self.state, pr())
        ap.process(self.runtime, self.state, pr(head='d' * 40))
        self.assertEqual(self.runtime.calls.count('confirm'), 2)

    def test_updated_head_first_settles_an_enqueued_old_revision(self):
        rev = self.state.revision(pr())
        rev['enqueued'] = True
        self.state.save()
        self.assertIs(self.state.revision(pr(head='d' * 40)), rev)

    def test_out_of_scope_never_fetches(self):
        result = ap.process(self.runtime, self.state, pr(paths=('tools/tool.py',)))
        self.assertTrue(result['done'])
        self.assertEqual(self.runtime.calls, [])
        self.assertEqual(self.runtime.messages[0][1], 'needs-maintainer')

    def test_intake_and_ai_failures_never_compile(self):
        self.runtime.intake_errors = ['synthetic lint reason']
        ap.process(self.runtime, self.state, pr())
        self.assertNotIn('screen', self.runtime.calls)
        self.assertNotIn('confirm', self.runtime.calls)
        self.runtime.intake_errors, self.runtime.unsafe = [], True
        ap.process(self.runtime, self.state, pr(head='e' * 40))
        self.assertNotIn('confirm', self.runtime.calls)
        self.assertIn('suspicious compiler construct', self.runtime.messages[-1][2])

    def test_function_limit_posts_changes_and_does_not_launch_model(self):
        self.runtime.reject = True
        ap.process(self.runtime, self.state, pr())
        self.assertNotIn('screen', self.runtime.calls)
        self.assertEqual(self.runtime.messages[-1][1], 'needs-changes')

    def test_function_failures_do_not_discard_the_rest(self):
        self.runtime.confirmed = dict(passed=['0x1000'], failed=[dict(rva='0x2000', reason='comparison failed')])
        ap.process(self.runtime, self.state, pr())
        self.assertIn('publish', self.runtime.calls)
        self.assertTrue(any('0x2000' in message for _, _, message in self.runtime.messages))

    def test_no_passes_or_approvals_never_publishes(self):
        self.runtime.confirmed = dict(passed=[], failed=[])
        ap.process(self.runtime, self.state, pr())
        self.assertNotIn('reviews', self.runtime.calls)
        self.runtime.confirmed = dict(passed=['0x1000'], failed=[])
        self.runtime.reviewed = dict(groups=[], failed=[dict(rva='0x1000', reason='blocking provenance')])
        ap.process(self.runtime, self.state, pr(head='e' * 40))
        self.assertNotIn('publish', self.runtime.calls)

    def test_caps_are_durable_and_roll_over_in_utc(self):
        self.state.reserve('compiles', 2)
        self.reload()
        with self.assertRaises(ap.Limit):
            self.state.reserve('compiles', 2)
        self.state.reserve('reviews', 2)
        with self.assertRaises(ap.Limit):
            self.state.reserve('reviews')
        tomorrow = ap.State(self.directory, self.config, '2026-01-02')
        tomorrow.reserve('compiles', 2)
        self.assertEqual(tomorrow.data['days']['2026-01-01']['compiles'], 2)

    def test_failed_operations_are_charged_and_not_checkpointed(self):
        revision = self.state.revision(pr())
        def operation():
            self.state.reserve('compiles', 2)
            raise OSError('crash')
        with self.assertRaises(OSError):
            self.state.once(revision, 'compile', operation)
        self.reload()
        with self.assertRaises(ap.Limit):
            self.state.once(self.state.revision(pr()), 'compile', operation)
        self.assertNotIn('compile', self.state.revision(pr())['completed'])

    def test_dry_run_completion_is_separate_from_live_state(self):
        ap.process(self.runtime, self.state, pr(), dry_run=True)
        ap.process(self.runtime, self.state, pr(), dry_run=False)
        self.assertEqual(self.runtime.calls.count('confirm'), 2)
        self.assertEqual(set(self.state.data['prs']), {'1', 'dry-1'})

    def test_lock_excludes_a_second_process(self):
        with ap.job_lock(self.directory):
            script = ('import sys;sys.path.insert(0,"tools");from pathlib import Path;'
                      'from contrib_autopilot import job_lock;\n'
                      'with job_lock(Path(sys.argv[1])): pass\n')
            proc = subprocess.run([sys.executable, '-c', script, str(self.directory)], cwd=ROOT,
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('another run-once', proc.stderr)
        with ap.job_lock(self.directory):
            pass


class PublicationAndScheduling(unittest.TestCase):
    def test_publication_filter_does_not_echo_private_material(self):
        for value in ('private /Users/synthetic/game', 'mov qword ptr [rax], rbx', '00 11 22 33',
                      'secret\nsecond line', 'a' * 400, 'code { body }'):
            self.assertIn('withheld', ap.safe_reason(value))
        self.assertEqual(ap.safe_reason('0x1234: comparison failed'), '0x1234: comparison failed')

    def test_launchd_is_private_and_not_loaded(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(ap.subprocess, 'run', side_effect=AssertionError('no install')):
            path, command = ap.write_launchd(ROOT, Path(tmp), sys.executable)
            data = plistlib.loads(path.read_bytes())
            self.assertEqual(data['StartInterval'], 600)
            self.assertFalse(data['RunAtLoad'])
            self.assertEqual(data['ProgramArguments'][-1], 'run-once')
            self.assertIn(str(path), command)
            self.assertTrue(command.startswith('launchctl bootstrap'))

    def test_wake_packet_both_ports(self):
        sock = Mock()
        with patch.object(ap.socket, 'socket') as factory:
            factory.return_value.__enter__.return_value = sock
            ap.wake_windows('E8:47:3A:E7:8F:EC', '192.168.1.255')
        calls = sock.sendto.call_args_list
        self.assertEqual([c.args[1][1] for c in calls], [9, 7])
        self.assertEqual(calls[0].args[0], b'\xff' * 6 + bytes.fromhex('E8473AE78FEC') * 16)

    def test_compiler_timeout_kills_child_and_does_not_leave_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(unit_build.UnitError) as cm:
                unit_build.compile_bounded([sys.executable, '-c',
                    'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);time.sleep(30)'],
                    tmp, dict(os.environ), timeout=0.1)
            self.assertEqual(cm.exception.code, 3)
            self.assertEqual(cm.exception.status, 'compile-timeout')
            self.assertFalse(any(p.is_file() for p in Path(tmp).rglob('*')))


class GitTransport(unittest.TestCase):
    """Real local git PR refs: attacker trees are never checked out or executed."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir()
        self.git('init', '--quiet', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Maintainer')
        self.git('config', 'user.email', 'maintainer@example.invalid')
        self.origin = Path(self.tmp.name) / 'origin.git'
        subprocess.run(['git', 'init', '--quiet', '--bare', str(self.origin)], check=True)
        (self.root / '.gitignore').write_text('.local/\n')
        (self.root / 'trusted.txt').write_text('trusted\n')
        self.git('add', '.gitignore', 'trusted.txt')
        self.git('commit', '--quiet', '-m', 'base')
        self.git('remote', 'add', 'origin', str(self.origin))
        self.git('push', '--quiet', 'origin', 'main')
        self.base = self.git('rev-parse', 'HEAD')
        self.private = self.root / '.local/contrib-autopilot'
        self.private.mkdir(parents=True)
        (self.root / '.local/verifier').mkdir()
        self.state = ap.State(self.private, ap.DEFAULTS)
        self.runtime = ap.Runtime(self.root, self.private, ap.DEFAULTS, self.state)
        self.git('checkout', '--quiet', '-b', 'contributor')
        self.git('config', 'user.name', 'Original Contributor')
        self.git('config', 'user.email', 'contributor@example.invalid')
        unit = self.root / 'reconstruction/synth/Synth.cpp'
        unit.parent.mkdir(parents=True)
        unit.write_text('// Original synthetic source\nint value;\n')
        self.git('add', 'reconstruction/synth/Synth.cpp')
        self.git('commit', '--quiet', '-m', 'contribute original source')
        self.head = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def test_fetch_materializes_only_blobs_on_trusted_main(self):
        fetched = self.runtime.fetch(pr(head=self.head))
        self.assertNotIn('problem', fetched)
        tree = Path(fetched['tree'])
        self.assertEqual(self.runtime.git(tree, 'rev-parse', 'HEAD'), self.base)
        self.assertEqual((tree / 'trusted.txt').read_text(), 'trusted\n')
        self.assertEqual((tree / 'reconstruction/synth/Synth.cpp').read_text(), '// Original synthetic source\nint value;\n')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)

    def test_unsafe_tip_and_historical_out_of_scope_are_refused(self):
        self.git('checkout', '--quiet', 'contributor')
        (self.root / 'reconstruction/synth/Synth.cpp').write_text('#pragma comment(lib,"malicious")\n')
        self.git('add', 'reconstruction/synth/Synth.cpp')
        self.git('commit', '--quiet', '-m', 'bad compiler input')
        bad = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', '--force', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')
        self.assertIn('deterministic screen', self.runtime.fetch(pr(head=bad))['problem'])
        self.git('checkout', '--quiet', 'contributor')
        self.git('reset', '--hard', self.head)
        (self.root / 'trusted.txt').write_text('attacker history\n')
        self.git('add', 'trusted.txt')
        self.git('commit', '--quiet', '-m', 'hidden tool change')
        (self.root / 'trusted.txt').write_text('trusted\n')
        self.git('add', 'trusted.txt')
        self.git('commit', '--quiet', '-m', 'hide change from tip diff')
        hidden = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', '--force', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')
        self.assertIn('history changes files outside', self.runtime.fetch(pr(head=hidden))['problem'])

    def contribution(self):
        return dict(head=self.head, base=self.base, authors=['Original Contributor <contributor@example.invalid>'],
                    paths=['reconstruction/synth/Synth.cpp'])

    def test_lane_merge_keeps_original_parent_and_exact_author_trailer(self):
        import flow_lane
        # Only the accepted data is in the index. PR source is not implicitly merged.
        (self.root / 'accepted.txt').write_text('accepted synthetic result\n')
        self.git('add', 'accepted.txt')
        request = dict(item='synthetic-item', contributor=self.contribution())
        flow_lane.commit_acceptance(self.root, [request], [dict(id='synthetic-item', root=str(self.root))],
                                    'Accept synthetic contribution', '2026-01-01T00:00:00+00:00')
        parents = self.git('rev-list', '--parents', '-n', '1', 'HEAD').split()[1:]
        self.assertEqual(parents, [self.base, self.head])
        self.assertEqual(self.git('show', self.head + ':reconstruction/synth/Synth.cpp'), '// Original synthetic source\nint value;')
        self.assertFalse((self.root / 'reconstruction/synth/Synth.cpp').exists())
        self.assertIn('Co-authored-by: Original Contributor <contributor@example.invalid>', self.git('log', '-1', '--format=%B'))
        self.assertEqual(self.git('log', '-1', '--format=%an <%ae>', self.head),
                         'Original Contributor <contributor@example.invalid>')
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_lane_refuses_forged_authorship_or_paths(self):
        import flow_lane
        for field, value in [('authors', ['Someone Else <someone@example.invalid>']), ('paths', ['tools/tool.py'])]:
            contribution = dict(self.contribution(), **{field: value})
            with self.subTest(field=field), self.assertRaises(Exception):
                flow_lane.contributor_history(self.root, self.root, contribution)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)


class RuntimeEffects(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.private = self.root / '.local/contrib-autopilot'
        self.private.mkdir(parents=True)
        self.state = ap.State(self.private, ap.DEFAULTS)
        with patch.object(ap, 'shared_root', return_value=self.root):
            self.runtime = ap.Runtime(self.root, self.private, ap.DEFAULTS, self.state)

    def test_dry_feedback_has_no_external_write_and_keeps_commit_sha(self):
        self.runtime.dry_run = True
        rev = self.state.revision(pr(), True)
        with patch.object(self.runtime, 'command', side_effect=AssertionError('no GitHub mutation')):
            self.runtime.feedback(rev, 'test', 'needs-changes', 'unsafe /Users/synthetic/file', commits=['c' * 40])
        body = rev['would_post']['test']['body']
        self.assertNotIn('/Users/', body)
        self.assertIn('c' * 40, body)

    def test_comment_recovery_finds_marker_before_posting_again(self):
        rev = self.state.revision(pr())
        marker = f'<!-- contrib-autopilot:1:{rev["head"]}:test -->'
        result = subprocess.CompletedProcess([], 0, json.dumps([[dict(body=marker, user=dict(login='awarebayes'))]]).encode(), b'')
        with patch.object(self.runtime, 'command', return_value=result), patch.object(self.runtime, 'gh') as gh:
            self.runtime.feedback(rev, 'test', 'needs-changes', 'synthetic reason')
        self.assertFalse(any(call.args[:2] == ('pr', 'comment') for call in gh.call_args_list))
        self.assertTrue(any(call.args[:2] == ('pr', 'edit') for call in gh.call_args_list))

    def test_model_uses_fresh_exact_model_and_read_only_sandbox(self):
        output = self.root / 'review.md'
        def command(argv, **kwargs):
            response = Path(argv[argv.index('--output-last-message') + 1])
            response.write_text('SAFE\nsynthetic\n')
            return subprocess.CompletedProcess(argv, 0, b'', b'')
        with patch.object(self.runtime, 'command', side_effect=command) as called:
            self.runtime.model(self.root, 'gpt-6.1-sol', 'synthetic diff', output)
        argv = called.call_args.args[0]
        self.assertEqual(argv[:2], ['codex', 'exec'])
        self.assertEqual(argv[argv.index('--model') + 1], 'gpt-6.1-sol')
        self.assertEqual(argv[argv.index('--sandbox') + 1], 'read-only')
        self.assertIn('--ephemeral', argv)
        self.assertNotIn('resume', argv)
        self.assertEqual(output.read_text(), 'SAFE\nsynthetic\n')
        self.assertEqual(self.state.data['days'][self.state.today]['reviews'], 1)

    def test_all_dropped_receipt_is_terminal_and_not_a_fake_acceptance(self):
        tree = self.root / 'tree'
        fdir = self.runtime.fdir
        ap.save_json(fdir / 'lane/queue/item.json', dict(id='item', root=str(tree), selection=['g1'], state='dropped', run='run1'))
        ap.save_json(fdir / 'lane/runs/run1.json', dict(state='done', integrated=None, dropped=[dict(item='item', reason='synthetic refusal')]))
        ap.save_json(fdir / 'groups/g1.json', dict(functions=['0x1000']))
        result = self.runtime.lane_result(tree, dict(groups=['g1']))
        self.assertTrue(result['settled'])
        self.assertEqual(result['accepted'], [])
        self.assertEqual(result['commits'], [])
        self.assertEqual(result['dropped'], 1)

    def test_green_receipt_after_crash_does_not_enqueue_or_push_again(self):
        tree = self.root / 'tree'
        fdir = self.runtime.fdir
        ap.save_json(fdir / 'lane/queue/item.json', dict(root=str(tree), selection=['g1'], state='done', run='run1'))
        ap.save_json(fdir / 'lane/runs/run1.json', dict(state='done', integrated=dict(ci='green', pushed='yes', commit='c' * 40),
                    accepted=[dict(group='g1', functions=['0x1000'])], dropped=[]))
        rev = self.state.revision(pr())
        rev['enqueued'] = True
        with patch.object(self.runtime, 'command', side_effect=AssertionError('must reuse green receipt')):
            result = self.runtime.publish(dict(tree=str(tree)), dict(groups=['g1']), rev)
        self.assertEqual(result['commits'], ['c' * 40])
        self.assertEqual(result['accepted'], ['0x1000'])


class SyntheticEndToEnd(unittest.TestCase):
    """Real git transport, state, review parser, sampling comparison and acceptance preparation.

    Only GitHub, model output and host/export commands are substituted. Comparator records are
    produced from the original synthetic COFF/PE fixtures, not hand-written success reports.
    """
    def setUp(self):
        import test_match_gate as fixture
        self.fixture = fixture
        self.kit = type('Kit', (fixture.GateFixture,), {'addCleanup': self.addCleanup})()
        self.kit.setUp()
        self.addCleanup(self.kit.tearDown)
        self.root = self.kit.root.resolve()
        self.kit.root = self.root
        self.kit.fn['status'] = 'mapped'
        (self.root / fixture.REVIEW).unlink()
        self.kit.write('data/progress.json', json.dumps(self.kit.data))
        self.kit.write('builds/target.json', json.dumps(self.kit.target))
        self.kit.write('docs/verification.md', (ROOT / 'docs/verification.md').read_bytes())
        self.kit.write('.gitignore', '.local/\n')
        self.kit.write('tools/trusted.txt', 'original trusted main tools\n')
        self.git('init', '--quiet', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Maintainer')
        self.git('config', 'user.email', 'maintainer@example.invalid')
        self.git('add', '.gitignore', 'builds', 'data', 'docs', 'findings', 'reconstruction', 'reports', 'tools')
        self.git('commit', '--quiet', '-m', 'synthetic baseline')
        self.origin = self.root / '.local/origin.git'
        self.origin.parent.mkdir(exist_ok=True)
        self.run_git('init', '--quiet', '--bare', str(self.origin))
        self.git('remote', 'add', 'origin', str(self.origin))
        self.git('push', '--quiet', 'origin', 'main')
        self.base = self.git('rev-parse', 'HEAD')
        self.git('checkout', '--quiet', '-b', 'contributor')
        self.git('config', 'user.name', 'Original Contributor')
        self.git('config', 'user.email', 'contributor@example.invalid')
        cpp = self.root / fixture.CPP
        cpp.write_text('// RVA 0x1010, 16 bytes\n// Recipe: reconstruction/recipes/synthetic.json\n' + cpp.read_text())
        self.git('add', fixture.CPP)
        self.git('commit', '--quiet', '-m', 'original synthetic contribution')
        self.head = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')
        ap.save_json(self.root / '.local/verifier/runners.json', dict(confirm=['mac', 'windows'], attempt='mac',
                     hosts={'mac': dict(backend='local'), 'windows': dict(backend='ssh')}))
        self.private = self.root / '.local/contrib-autopilot'
        self.private.mkdir()
        self.state = ap.State(self.private, ap.DEFAULTS)
        self.runtime = ap.Runtime(self.root, self.private, ap.DEFAULTS, self.state, dry_run=True)
        self.commands, self.models = [], []
        self.real_command = self.runtime.command
        self.runtime.command = self.command
        self.runtime.model = self.model

    def run_git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def git(self, *args):
        return self.run_git(*args)

    def command(self, argv, cwd=None, **kwargs):
        argv = list(map(str, argv))
        cwd = Path(cwd or self.root)
        self.commands.append(argv)
        output = b''
        if argv[0] == 'gh':
            self.assertEqual(argv[1:3], ['pr', 'view'])
            output = json.dumps(dict(headRefOid=self.head, state='OPEN')).encode()
        elif len(argv) > 1 and argv[1] == 'tools/contrib.py':
            self.assertIn('--base', argv)
            self.assertIn('origin/main', argv)
            self.assertIn('contrib/pr-1', argv)
            output = b'{"problems": [], "ok": true}'
        elif len(argv) > 1 and argv[1] == 'tools/ghidra/export_pack.py':
            rows = Path(argv[3]).read_text().splitlines()
            for row in rows:
                build, rva, tid, cpp, recipe = row.split()
                self.assertEqual(recipe, 'recipe=synthetic')
                ap.save_json(cwd / '.local/tasks' / tid / 'task.json', dict(task_id=tid, build_id=build,
                             compiled=cpp, recipe=self.fixture.RECIPE, symbols='symbols.json',
                             functions=[dict(rva=rva, size=self.kit.fn['size'], symbol='SyntheticSum')]))
        elif len(argv) > 1 and argv[1] == 'tools/verifier/attempt':
            pass
        elif len(argv) > 1 and argv[1] == 'tools/verifier/bind.py':
            directory = Path(Path(argv[argv.index('--list') + 1]).read_text().strip())
            task = ap.read_json(directory / 'task.json')
            task['symbols'] = self.fixture.MAP
            ap.save_json(directory / 'task.json', task)
        elif len(argv) > 1 and argv[1] == 'tools/verifier/confirm':
            output_dir = Path(argv[argv.index('--out') + 1])
            original = self.kit.root
            try:
                self.kit.root = cwd
                self.kit.record = self.kit.make_record()
                self.kit.record['build'] = self.kit.build_block()
            finally:
                self.kit.root = original
            ap.save_json(output_dir / 'synthetic-fixture/0x1010.json', self.kit.record)
        elif len(argv) > 1 and argv[1] == 'tools/verifier/runners.py':
            pass
        else:
            return self.real_command(argv, cwd=cwd, **kwargs)
        return subprocess.CompletedProcess(argv, 0, output, b'')

    def model(self, tree, model, prompt, output):
        self.state.reserve('reviews')
        self.models.append(model)
        if output.name == 'engineer-screen.txt':
            document = 'SAFE\nOriginal synthetic programmer source.\n'
        else:
            import source_digest
            task = output.stem
            document = f'''# Review {task}

reviewer_model: {model}
fresh_context: yes
drafted_or_triaged_any_reviewed_function: no
gates_in_force: claude-low
source_revision: {self.base}
sampling_second_pass: {'yes' if task.endswith('-s') else 'no'}
decompiler_output_read: no

## synthetic-fixture 0x1010 {self.kit.fn['size']}

verdict: approve
escalation_category: none
review_kind: full
source_paths: {self.fixture.CPP} {self.fixture.HDR}
source_digest: {source_digest.tu_digest(tree, [self.fixture.CPP, self.fixture.HDR])}
report_path: {self.fixture.RECORD}
report_binding: agree, synthetic comparator reports
checks:
  plausible_source: pass, synthetic
  provenance: pass, original synthetic fixture
  claim_scope: pass, byte match only
  publication_hygiene: pass, original fixture only
blocking_findings: none
naming_findings: none
reasons: original synthetic source and comparator reports
'''
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document)
        return document

    def test_dry_run_reaches_real_acceptance_without_post_merge_or_push(self):
        result = ap.process(self.runtime, self.state,
                            pr(head=self.head, paths=(self.fixture.CPP,)), dry_run=True)
        self.assertTrue(result['done'])
        published = result['completed']['publication']
        self.assertEqual(published['accepted'], 1)
        self.assertEqual(published['dropped'], 0)
        self.assertEqual(self.models, ['gpt-6.1-sol', 'gpt-6.1-terra', 'gpt-6.1-sol'])
        self.assertEqual(self.state.data['days'][self.state.today], dict(compiles=5, reviews=3))
        self.assertEqual(self.git('rev-parse', 'origin/main'), self.base)
        self.assertFalse((self.root / '.local/flow/lane/queue').exists())
        self.assertFalse((self.root / '.local/flow/groups').exists())
        for argv in self.commands:
            if argv[0] == 'gh':
                self.assertEqual(argv[1:3], ['pr', 'view'])
            if argv[0] == 'git':
                self.assertNotIn(argv[1], ('merge', 'commit-tree', 'push', 'commit'))
                if argv[1] == 'checkout':
                    self.assertEqual(argv[-1], self.base)
        tree = Path(result['completed']['fetch']['tree'])
        self.assertEqual(ap.read_json(tree / 'data/progress.json')['functions'][0]['status'], 'mapped')
        self.assertFalse((tree / self.fixture.REVIEW).exists())
        # Checkpointed dry run resumes without a second model call or compiler invocation.
        ap.process(self.runtime, ap.State(self.private, ap.DEFAULTS), pr(head=self.head, paths=(self.fixture.CPP,)), True)
        self.assertEqual(len(self.models), 3)


class RecoveryRegression(unittest.TestCase):
    setUp = GitTransport.setUp
    git = GitTransport.git

    def test_interrupted_initial_clone_is_retained_and_reinitialized(self):
        original = self.runtime.link_inputs
        with patch.object(self.runtime, 'link_inputs', side_effect=OSError('interrupted linking')):
            with self.assertRaises(OSError):
                self.runtime.fetch(pr(head=self.head))
        fetched = self.runtime.fetch(pr(head=self.head))
        tree = Path(fetched['tree'])
        self.assertTrue((tree / '.local/contrib-initialized.json').is_file())
        self.assertTrue(list(tree.parent.glob('tree-interrupted-*')))
        self.assertEqual(self.runtime.git(tree, 'rev-parse', 'HEAD'), self.base)

    def test_frozen_enqueued_revision_ignores_new_out_of_scope_metadata(self):
        runtime = FakeRuntime()
        runtime.crash = 'publish'
        with self.assertRaises(OSError):
            ap.process(runtime, self.state, pr(head=self.head))
        runtime.crash = None
        revised = pr(head='e' * 40, paths=('tools/attacker.py',))
        result = ap.process(runtime, self.state, revised)
        self.assertEqual(result['head'], self.head)
        self.assertIn('finish', runtime.calls)
        self.assertFalse(runtime.messages)

    def test_closed_unqueued_revision_is_abandoned_and_releases_contributor(self):
        runtime = FakeRuntime()
        result = ap.process(runtime, self.state, dict(pr(), state='CLOSED'))
        self.assertTrue(result['done'])
        self.assertTrue(result['abandoned'])
        self.assertFalse(runtime.calls)

    def test_scheduler_discovers_a_merged_pending_receipt(self):
        revision = self.state.revision(pr(head=self.head))
        revision['enqueued'] = True
        self.state.save()
        runtime = Mock()
        runtime.list_prs.return_value = []
        runtime.view_pr.return_value = dict(pr(head=self.head), state='MERGED')
        with patch.object(ap, 'Runtime', return_value=runtime), patch.object(ap, 'process', return_value={'done': True}) as process:
            self.assertEqual(ap.main(['--root', str(self.root), 'run-once']), 0)
        self.assertEqual(process.call_args.args[2]['state'], 'MERGED')
        runtime.require_account.assert_called_once()

    def test_transient_confirm_status_is_not_a_completed_negative(self):
        for code, output in [(2, b'configuration unavailable'), (1, b'  ERROR transport unavailable\n')]:
            with self.subTest(code=code), self.assertRaises(ap.Stop):
                ap.Runtime.require_comparison(subprocess.CompletedProcess([], code, output, b''))
        ap.Runtime.require_comparison(subprocess.CompletedProcess([], 1, b'NOT REPRODUCED host=fail\n', b''))

    def test_dry_reviews_do_not_enter_the_live_hold_store(self):
        self.runtime.dry_run = True
        fetched = self.runtime.fetch(pr(head=self.head))
        private_reviews = Path(fetched['tree']) / '.local/reviews'
        self.assertFalse(private_reviews.is_symlink())
        (private_reviews / 'dry-review.md').write_text('original synthetic rejection\n')
        self.assertFalse((self.root / '.local/reviews/dry-review.md').exists())


def _pid_running(pid):
    if sys.platform == 'win32':
        import csv
        result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                                capture_output=True, text=True, timeout=5)
        return any(len(row) > 1 and row[1] == str(pid) for row in csv.reader(result.stdout.splitlines()))
    result = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True, timeout=5)
    return result.returncode == 0 and not result.stdout.strip().startswith('Z')


class CompileSupervisorRegression(unittest.TestCase):
    def test_root_exit_still_terminates_descendant_holding_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / 'child.pid'
            command = ('import subprocess,sys;from pathlib import Path;'
                       'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);'
                       f'Path({str(pidfile)!r}).write_text(str(p.pid))')
            started = time.monotonic()
            result = unit_build.compile_bounded([sys.executable, '-c', command], tmp, dict(os.environ), timeout=0.5)
            self.assertEqual(result.returncode, 0)
            self.assertLess(time.monotonic() - started, 4)
            self.assertFalse(_pid_running(int(pidfile.read_text())))

    def test_dead_outer_supervisor_does_not_cancel_the_child_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / 'child.pid'
            payload = ('import os,time;from pathlib import Path;'
                       f'Path({str(pidfile)!r}).write_text(str(os.getpid()));time.sleep(30)')
            runner = ('import os,sys;sys.path.insert(0,' + repr(str(ROOT / 'tools/verifier')) + ');'
                      'import unit_build;unit_build.compile_bounded('
                      + repr([sys.executable, '-c', payload]) + ',' + repr(tmp) + ',dict(os.environ),timeout=0.5)')
            proc = subprocess.Popen([sys.executable, '-c', runner], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 3
                while not pidfile.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(pidfile.exists())
                pid = int(pidfile.read_text())
                proc.kill()
                proc.wait(timeout=2)
                deadline = time.monotonic() + 3
                while _pid_running(pid) and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertFalse(_pid_running(pid))
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=2)

    def test_failed_windows_job_setup_never_launches_a_compiler(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(unit_build.sys, 'platform', 'win32'), \
                patch.object(unit_build, 'windows_compile_job', side_effect=OSError('job refused')), \
                patch.object(unit_build.subprocess, 'run', side_effect=AssertionError('must not compile')):
            result = Path(tmp) / 'result.json'
            self.assertEqual(unit_build.compile_supervisor(['unused'], 0.1, result), 125)
            self.assertTrue(json.loads(result.read_text())['supervisor_error'])


# Exercise an actual transport refusal at both confirmation stages in the end-to-end fixture.
def _test_transient_confirm_resume(self):
    original = self.runtime.command
    count = 0
    def command(argv, **kwargs):
        nonlocal count
        if len(argv) > 1 and argv[1] == 'tools/verifier/confirm':
            count += 1
            if count == 1:
                return subprocess.CompletedProcess(argv, 2, b'transport unavailable', b'')
        return original(argv, **kwargs)
    self.runtime.command = command
    row = pr(head=self.head, paths=(self.fixture.CPP,))
    with self.assertRaises(ap.Stop):
        ap.process(self.runtime, self.state, row, True)
    self.assertNotIn('confirmation', self.state.revision(row, True)['completed'])
    result = ap.process(self.runtime, self.state, row, True)
    self.assertEqual(result['completed']['publication']['accepted'], 1)
    self.assertEqual(self.models, ['gpt-6.1-sol', 'gpt-6.1-terra', 'gpt-6.1-sol'])


SyntheticEndToEnd.test_transient_confirmation_resumes_same_head = _test_transient_confirm_resume


class EnqueueIntentRegression(unittest.TestCase):
    setUp = RuntimeEffects.setUp

    def crash_after_real_enqueue(self):
        import flow_lane
        fake = FakeRuntime()
        original_fetch = fake.fetch
        def fetch(row):
            result = original_fetch(row)
            result['tree'] = str(self.root / 'tree')
            return result
        fake.fetch = fetch
        fake.publish = self.runtime.publish
        self.runtime.current_head = lambda number: 'a' * 40
        def command(argv, **kwargs):
            self.assertEqual(argv[1:3], ['tools/flow.py', 'integrate'])
            flow_lane.enqueue(self.root / 'tree', self.runtime.fdir, 'review', ['g1'], approved_only=True)
            raise OSError('crash after real durable enqueue, before returning to autopilot')
        self.runtime.command = command
        with self.assertRaises(OSError):
            ap.process(fake, self.state, pr())
        self.state = ap.State(self.private, ap.DEFAULTS)
        revision = self.state.data['prs']['1']
        self.assertTrue(revision['enqueued'])
        self.assertTrue(list((self.runtime.fdir / 'lane/queue').glob('*.json')))
        self.assertNotIn('publication', revision['completed'])
        fake.publish = FakeRuntime.publish.__get__(fake, FakeRuntime)
        return fake

    def test_enqueue_crash_then_new_head_keeps_frozen_receipt(self):
        fake = self.crash_after_real_enqueue()
        result = ap.process(fake, self.state, pr(head='e' * 40, paths=('tools/attacker.py',)))
        self.assertEqual(result['head'], 'a' * 40)
        self.assertTrue(result['done'])
        self.assertIn('finish', fake.calls)
        self.assertFalse(fake.messages)

    def test_enqueue_crash_then_merged_pr_still_finishes_receipt(self):
        fake = self.crash_after_real_enqueue()
        result = ap.process(fake, self.state, dict(pr(), state='MERGED'))
        self.assertTrue(result['done'])
        self.assertNotIn('abandoned', result)
        self.assertIn('finish', fake.calls)


if __name__ == '__main__':
    unittest.main()
