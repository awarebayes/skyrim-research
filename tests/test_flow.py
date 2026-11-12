"""Tests for tools/flow.py: state derivation, review groups and sampling, next-actions ordering,
and scripted integration (refusals and a full run against stub tools and a local bare remote).
All inputs are synthetic."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import flow  # noqa: E402
from source_digest import tu_digest  # noqa: E402
import work_queue as wq  # noqa: E402

BUILD = 'synthetic-build'
FUNCS = [(0x1000, 16, 'Foo::A'), (0x1010, 8, 'Foo::B'), (0x2000, 12, 'Bar::C')]

STUB_ACCEPT = r'''
import json, sys
from pathlib import Path
review = sys.argv[sys.argv.index('--review') + 1]
data = json.loads(Path('data/progress.json').read_text())
changed = ['data/progress.json']
text = Path(review).read_text()
for fn in data['functions']:
    block = f"## {fn['build_id']} 0x{fn['rva']:x} {fn['size']}\n\nverdict: approve"
    if block in text:
        fn['status'] = 'matched'
        rec = Path(f"reports/{fn['build_id']}/0x{fn['rva']:x}.review.json")
        rec.write_text(json.dumps({'verdict': 'approve'}) + '\n')
        changed.append(rec.as_posix())
Path('data/progress.json').write_text(json.dumps(data, indent=2) + '\n')
print('accepted')
print('changed files (stage these by name; nothing was committed):')
for c in changed:
    print('  ' + c)
'''


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def review_text(task, blocks, sampling='no'):
    out = [f'# Review {task}', '', 'reviewer_model: test-model', 'fresh_context: yes',
           'drafted_or_triaged_any_reviewed_function: no', 'gates_in_force: G2', 'source_revision: abc',
           f'sampling_second_pass: {sampling}', 'decompiler_output_read: no', '']
    for (rva, size, digest, verdict, cat) in blocks:
        check = 'pass' if verdict == 'approve' else 'fail'
        out += [f'## {BUILD} 0x{rva:x} {size}', '', f'verdict: {verdict}', f'escalation_category: {cat}',
                'review_kind: full', 'source_paths: reconstruction/x/Foo.cpp', f'source_digest: {digest}',
                f'report_path: reports/{BUILD}/0x{rva:x}.json', 'report_binding: agree, ok',
                'checks:', '  plausible_source: pass, ok', f'  provenance: {check}, x',
                '  claim_scope: pass, ok', '  publication_hygiene: pass, ok',
                'blocking_findings: none' if verdict == 'approve' else 'blocking_findings:\n  - licence notice cut short',
                'naming_findings: none', 'reasons: synthetic', '']
    return '\n'.join(out) + '\n'


class Repo:
    """A tiny repository with an inventory, two units, match records and an origin remote."""

    def __init__(self, tmp, confirmed=(0x1000, 0x1010, 0x2000)):
        self.tmp = tmp
        self.root = tmp / 'repo'
        self.origin = tmp / 'origin.git'
        r = self.root
        (r / 'reconstruction/x').mkdir(parents=True)
        (r / 'reconstruction/x/Foo.cpp').write_text('int a;\n')
        (r / 'reconstruction/x/Foo.h').write_text('#pragma once\n')
        (r / 'reconstruction/x/Bar.cpp').write_text('int c;\n')
        (r / 'reports' / BUILD).mkdir(parents=True)
        (r / 'docs').mkdir()
        (r / 'docs/verification.md').write_text('Reviewer subagent, Opus class.\n')
        (r / 'tools').mkdir()
        (r / 'tools/accept_function.py').write_text(STUB_ACCEPT)
        for name in ('check.py', 'build_site.py', 'ci_status.py'):
            (r / 'tools' / name).write_text('import sys\nsys.exit(0)\n')
        (r / 'tests').mkdir()
        (r / 'tests/test_ok.py').write_text('import unittest\nclass T(unittest.TestCase):\n    def test(self):\n        pass\n')
        (r / '.gitignore').write_text('.local/\n')
        fns = []
        for rva, size, name in FUNCS:
            fn = {'id': f'{BUILD}-0x{rva:x}', 'build_id': BUILD, 'rva': rva, 'size': size, 'status': 'mapped', 'name': name}
            if rva in confirmed:
                unit = ['reconstruction/x/Foo.cpp', 'reconstruction/x/Foo.h'] if rva < 0x2000 else ['reconstruction/x/Bar.cpp']
                rec = {'source': {'compiled': unit[0], 'translation_unit': unit, 'digest': tu_digest(r, unit)},
                       'recipe': {'sha256': 'r' * 64}, 'toolchain_pin': {'sha256': 't' * 64},
                       'runs': [{'compiled_on': 'host-a'}, {'compiled_on': 'host-b'}]}
                (r / f'reports/{BUILD}/0x{rva:x}.json').write_text(json.dumps(rec))
                fn['report'] = f'reports/{BUILD}/0x{rva:x}.json'
            fns.append(fn)
        (r / 'data').mkdir()
        (r / 'data/progress.json').write_text(json.dumps({'target_build_id': BUILD, 'functions': fns}, indent=2) + '\n')
        git(tmp, 'init', '--quiet', '--bare', str(self.origin))
        git(r, 'init', '--quiet', '-b', 'main')
        git(r, 'config', 'user.email', 't@example.invalid')
        git(r, 'config', 'user.name', 'test')
        git(r, 'add', '-A')
        git(r, 'commit', '--quiet', '-m', 'base')
        git(r, 'remote', 'add', 'origin', str(self.origin))
        git(r, 'push', '--quiet', 'origin', 'main')
        self.fdir = r / '.local/flow'

    def digest(self, rva):
        return json.loads((self.root / f'reports/{BUILD}/0x{rva:x}.json').read_text())['source']['digest']

    def save_review(self, task, blocks, sampling='no'):
        path = self.root / '.local/reviews' / f'{task}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(review_text(task, blocks, sampling))
        return path


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.repo = Repo(self.tmp)
        self.root, self.fdir, self.origin = self.repo.root, self.repo.fdir, self.repo.origin

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def actions(self):
        return flow.next_actions(self.root, self.fdir, now=0)

    def test_session_start_comes_first_then_grouping(self):
        acts = self.actions()
        self.assertEqual(acts[0], ('run', 'python3 tools/flow.py session-start'))
        self.assertIn(('run', 'python3 tools/flow.py review-group'), acts)

    def test_states_confirmed_and_stale(self):
        states = flow.function_states(self.root, self.fdir)
        self.assertEqual({r: s['state'] for r, s in states.items()},
                         {'0x1000': 'confirmed', '0x1010': 'confirmed', '0x2000': 'confirmed'})
        (self.root / 'reconstruction/x/Bar.cpp').write_text('int c2;\n')
        self.assertEqual(flow.function_states(self.root, self.fdir)['0x2000']['state'], 'confirm-stale')

    def test_one_host_is_not_confirmed(self):
        path = self.root / f'reports/{BUILD}/0x2000.json'
        rec = json.loads(path.read_text())
        rec['runs'] = [{'compiled_on': 'host-a'}, {'compiled_on': 'host-a'}]
        path.write_text(json.dumps(rec))
        self.assertEqual(flow.function_states(self.root, self.fdir)['0x2000']['state'], 'confirm-stale')

    def test_review_group_keeps_units_together_and_samples_first_twenty(self):
        made = flow.review_group(self.root, self.fdir, max_size=2)
        self.assertEqual(len(made), 2)
        g1, g2 = (flow.load_group(self.fdir, n) for n in made)
        self.assertEqual(sorted(g1['functions'] + g2['functions']), ['0x1000', '0x1010', '0x2000'])
        self.assertIn(sorted(g1['functions']), (['0x1000', '0x1010'], ['0x2000']))
        # Nothing accepted yet under these versions: every function is in its first 20, so sampled.
        self.assertEqual(sorted(g1['sampled']), sorted(g1['functions']))
        self.assertTrue((self.root / g1['brief']).is_file())
        s = flow.load_group(self.fdir, g1['pair'])
        self.assertEqual((s['kind'], s['reviewer_model']), ('sampling', 'opus'))
        self.assertIn('sampling_second_pass: yes', (self.root / s['brief']).read_text())
        self.assertTrue((self.root / f'.local/briefs/rerun-{g1["name"]}.md').is_file())
        # Grouped functions are not grouped twice.
        self.assertEqual(flow.review_group(self.root, self.fdir), [])

    def test_baseline_ends_first_twenty_sampling(self):
        flow.review_group(self.root, self.fdir, max_size=1)
        g = flow.load_group(self.fdir, 'g001')
        comps = g['components'][g['functions'][0]]
        v = {'baseline': {c: {val: 100} for c, val in comps.items()}}
        shutil.rmtree(self.fdir / 'groups')
        (self.fdir / 'versions.json').write_text(json.dumps(v))
        flow.review_group(self.root, self.fdir, max_size=3)
        g = flow.load_group(self.fdir, 'g001')
        # ceil(5% of 3) = 1 random pick, nothing more.
        self.assertEqual(len(g['sampled']), 1)

    def test_reviewer_model_must_be_admitted_by_the_rule(self):
        with self.assertRaises(flow.FlowError):
            flow.review_group(self.root, self.fdir, reviewer_model='sonnet')
        with self.assertRaises(flow.FlowError):
            flow.review_group(self.root, self.fdir, reviewer_model='gpt-6.1-terra')
        (self.root / 'docs/verification.md').write_text('a Reviewer of Sonnet class by default\n')
        made = flow.review_group(self.root, self.fdir, reviewer_model='sonnet')
        self.assertEqual(flow.load_group(self.fdir, made[0])['reviewer_model'], 'sonnet')

    def test_claude_low_profile_falls_back_to_opus_until_admitted(self):
        flow.log_event(self.fdir, 'session-start', profile='claude-low')
        made = flow.review_group(self.root, self.fdir)
        self.assertEqual(flow.load_group(self.fdir, made[0])['reviewer_model'], 'opus')
        (self.root / 'docs/verification.md').write_text('admits the Terra class as the Reviewer\n')
        shutil.rmtree(self.fdir / 'groups')
        made = flow.review_group(self.root, self.fdir)
        g = flow.load_group(self.fdir, made[0])
        self.assertEqual((g['reviewer_model'], g['reviewer_harness']), ('gpt-6.1-terra', 'codex'))
        flow.log_event(self.fdir, 'session-start', profile='claude-low')
        line = [t for k, t in self.actions() if k == 'dispatch' and f'Reviewer for {g["name"]}:' in t][0]
        self.assertIn('Codex session', line)
        self.assertIn('docs/reviewer-runbook.md', line)

    def grouped(self):
        flow.log_event(self.fdir, 'session-start')
        name = flow.review_group(self.root, self.fdir, max_size=3)[0]
        return flow.load_group(self.fdir, name)

    def test_dispatch_then_wait_then_integrate_after_sampling(self):
        g = self.grouped()
        acts = self.actions()
        self.assertTrue(any(k == 'dispatch' and f'flow.py dispatched {g["name"]}' in t for k, t in acts))
        self.assertTrue(any(k == 'dispatch' and 'sampling re-run' in t for k, t in acts))
        g['dispatched'] = 'x'
        g['rerun_dispatched'] = 'x'
        flow.save_group(self.fdir, g)
        self.assertTrue(any(k == 'wait' and g['task_id'] in t for k, t in self.actions()))
        blocks = [(r, s, self.repo.digest(r), 'approve', 'none') for r, s, _ in FUNCS]
        self.repo.save_review(g['task_id'], blocks)
        self.assertEqual(flow.function_states(self.root, self.fdir)['0x1000']['state'], 'approved')
        # Sampled functions: no integration until the second review and the re-run agree.
        self.assertFalse(any(t == f'python3 tools/flow.py integrate {g["name"]}' for _, t in self.actions()))
        self.repo.save_review(f'{g["task_id"]}-s', [b for b in blocks if f'0x{b[0]:x}' in g['sampled']], 'yes')
        cmp = self.root / 'cmp.txt'
        cmp.write_text(''.join(f'{r} AGREE\n' for r in g['sampled']))
        flow.record_rerun(self.root, self.fdir, g['name'], cmp)
        self.assertIn(('run', f'python3 tools/flow.py integrate {g["name"]}'), self.actions())

    def test_sampling_disagreement_is_a_stop(self):
        g = self.grouped()
        self.repo.save_review(g['task_id'], [(r, s, self.repo.digest(r), 'approve', 'none') for r, s, _ in FUNCS])
        second = [(r, s, self.repo.digest(r), 'reject' if r == 0x1000 else 'approve', 'none') for r, s, _ in FUNCS]
        self.repo.save_review(f'{g["task_id"]}-s', second, 'yes')
        stops = [t for k, t in self.actions() if k == 'stop']
        self.assertTrue(any('sampling disagreement' in t for t in stops), stops)
        with self.assertRaises(flow.FlowError):
            flow.integrate(self.root, self.fdir, g['name'], python=sys.executable)

    def test_rerun_disagree_is_a_stop(self):
        g = self.grouped()
        blocks = [(r, s, self.repo.digest(r), 'approve', 'none') for r, s, _ in FUNCS]
        self.repo.save_review(g['task_id'], blocks)
        self.repo.save_review(f'{g["task_id"]}-s', blocks, 'yes')
        cmp = self.root / 'cmp.txt'
        cmp.write_text(''.join(f'{r} {"DISAGREE" if i == 0 else "AGREE"}\n' for i, r in enumerate(g['sampled'])))
        flow.record_rerun(self.root, self.fdir, g['name'], cmp)
        self.assertTrue(any(k == 'stop' and 're-run did not agree' in t for k, t in self.actions()))

    def test_blocking_escalation_holds_the_group(self):
        g = self.grouped()
        blocks = [(r, s, self.repo.digest(r), 'escalate' if r == 0x2000 else 'approve',
                   'legal' if r == 0x2000 else 'none') for r, s, _ in FUNCS]
        self.repo.save_review(g['task_id'], blocks)
        acts = self.actions()
        self.assertTrue(any(k == 'stop' and 'legal' in t for k, t in acts))
        self.assertFalse(any('integrate' in t for _, t in acts))
        with self.assertRaisesRegex(flow.FlowError, 'blocking escalation'):
            flow.integrate(self.root, self.fdir, g['name'], python=sys.executable)

    def test_malformed_review_asks_for_a_new_reviewer_never_an_edit(self):
        g = self.grouped()
        path = self.repo.save_review(g['task_id'], [(r, s, self.repo.digest(r), 'approve', 'none') for r, s, _ in FUNCS])
        path.write_text(path.read_text().replace('verdict: approve', 'verdict: Approve', 1))
        self.assertTrue(any(f'redo-review {g["name"]}' in t for _, t in self.actions()))
        with self.assertRaisesRegex(flow.FlowError, 'redo-review'):
            flow.integrate(self.root, self.fdir, g['name'], python=sys.executable)
        g2 = flow.redo_review(self.root, self.fdir, g['name'])
        self.assertEqual(g2['task_id'], f'{g["task_id"]}-r2')
        self.assertEqual(flow.redo_review(self.root, self.fdir, g['name'])['task_id'], f'{g["task_id"]}-r3')

    def test_missing_review_is_refused(self):
        g = self.grouped()
        with self.assertRaisesRegex(flow.FlowError, 'not saved'):
            flow.integrate(self.root, self.fdir, g['name'], python=sys.executable)

    def test_earlier_reject_of_same_source_holds_function(self):
        self.repo.save_review('review-old', [(0x2000, 12, self.repo.digest(0x2000), 'reject', 'none')])
        states = flow.function_states(self.root, self.fdir)
        self.assertEqual(states['0x2000']['state'], 'rejected')
        made = flow.review_group(self.root, self.fdir)
        self.assertNotIn('0x2000', flow.load_group(self.fdir, made[0])['functions'])
        self.assertTrue(any('brief triage --held' in t for _, t in self.actions()))

    def integrate_ready(self):
        g = self.grouped()
        flow.save_group(self.fdir, dict(g, sampled=[], pair=None))
        blocks = [(r, s, self.repo.digest(r), 'reject' if r == 0x2000 else 'approve', 'none') for r, s, _ in FUNCS]
        self.repo.save_review(g['task_id'], blocks)
        return g

    def test_integrate_runs_every_step_and_records_it(self):
        g = self.integrate_ready()
        # An unrelated working-tree change is never staged.
        (self.root / 'reconstruction/x/Other.cpp').write_text('int other;\n')
        flow.integrate(self.root, self.fdir, g['name'], python=sys.executable, ci_wait=0)
        g = flow.load_group(self.fdir, g['name'])
        integ = g['integrated']
        self.assertEqual((integ['accepted'], integ['ci']), (2, 'green'))
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), git(self.origin, 'rev-parse', 'main'))
        self.assertIn('reconstruction/x/Other.cpp', git(self.root, 'status', '--porcelain'))
        self.assertIn(f'reports/{BUILD}/0x1000.review.json', integ['files'])
        states = flow.function_states(self.root, self.fdir)
        self.assertEqual(states['0x1000']['state'], 'pushed')
        self.assertEqual(states['0x2000']['state'], 'rejected')
        self.assertFalse(any('integrate' in t for _, t in self.actions()))
        self.assertTrue(any('brief triage --group' in t for _, t in self.actions()))

    def test_integrate_stops_at_failed_check_and_commits_nothing(self):
        g = self.integrate_ready()
        (self.root / 'tools/check.py').write_text('import sys\nprint("Stale acceptance")\nsys.exit(1)\n')
        git(self.root, 'commit', '--quiet', '-am', 'failing check')
        git(self.root, 'push', '--quiet', 'origin', 'main')
        head = git(self.root, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(flow.FlowError, 'STOPPED at check.py --staged'):
            flow.integrate(self.root, self.fdir, g['name'], python=sys.executable)
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), head)
        self.assertEqual(git(self.root, 'diff', '--cached', '--name-only'), '')

    def test_integrate_refuses_when_not_level_with_origin(self):
        g = self.integrate_ready()
        (self.root / 'x.txt').write_text('x')
        git(self.root, 'add', 'x.txt')
        git(self.root, 'commit', '--quiet', '-m', 'local only')
        with self.assertRaisesRegex(flow.FlowError, 'not level'):
            flow.integrate(self.root, self.fdir, g['name'], python=sys.executable)

    def test_integrate_stops_on_red_ci_and_resumes(self):
        g = self.integrate_ready()
        (self.root / 'tools/ci_status.py').write_text('import sys\nprint("RED")\nsys.exit(1)\n')
        git(self.root, 'commit', '--quiet', '-am', 'red ci stub')
        git(self.root, 'push', '--quiet', 'origin', 'main')
        with self.assertRaisesRegex(flow.FlowError, 'CI RED'):
            flow.integrate(self.root, self.fdir, g['name'], python=sys.executable, ci_wait=0)
        integ = flow.load_group(self.fdir, g['name'])['integrated']
        self.assertTrue(integ['pushed'])
        (self.root / 'tools/ci_status.py').write_text('import sys\nsys.exit(0)\n')
        flow.integrate(self.root, self.fdir, g['name'], python=sys.executable, ci_wait=0)
        self.assertEqual(flow.load_group(self.fdir, g['name'])['integrated']['ci'], 'green')

    def test_integrate_no_push_stops_after_clean_checks(self):
        g = self.integrate_ready()
        flow.integrate(self.root, self.fdir, g['name'], push=False, python=sys.executable)
        integ = flow.load_group(self.fdir, g['name'])['integrated']
        self.assertTrue(integ['checks'])
        self.assertIsNone(integ['pushed'])
        self.assertNotEqual(git(self.root, 'rev-parse', 'HEAD'), git(self.origin, 'rev-parse', 'main'))


class QueueStates(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.repo = Repo(self.tmp, confirmed=())
        self.root, self.fdir, self.origin = self.repo.root, self.repo.fdir, self.repo.origin
        q = self.root / '.local/queue/small'
        q.mkdir(parents=True)
        (q / 'queue.tsv').write_text('.local/tasks/g/g-foo\treconstruction/x/Foo.h,reconstruction/x/Foo.cpp\t0x1000,0x1010\t3\n'
                                     '.local/tasks/g/g-bar\treconstruction/x/Bar.cpp\t0x2000\t3\n')
        self.q = q

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_queue_states_and_profile_ladder(self):
        flow.log_event(self.fdir, 'session-start')
        st = flow.function_states(self.root, self.fdir)
        self.assertEqual(st['0x1000']['state'], 'queued')
        self.assertTrue(any('brief drafter --profile cheap' in t for _, t in flow.next_actions(self.root, self.fdir)))
        wq.claim(self.q, 'haiku-1', profile='cheap')
        self.assertEqual(flow.function_states(self.root, self.fdir)['0x1000']['state'], 'drafting')
        wq.finish(self.q, '.local/tasks/g/g-foo', [json.dumps({'rva': '0x1000', 'result': 'pass', 'attempts': 1}),
                                                     json.dumps({'rva': '0x1010', 'result': 'fail', 'attempts': 3}),
                                                     json.dumps({'unit': 'reconstruction/x/Foo.cpp'})])
        st = flow.function_states(self.root, self.fdir)
        self.assertEqual((st['0x1000']['state'], st['0x1010']['state']), ('drafted-pass', 'draft-failed'))
        acts = [t for _, t in flow.next_actions(self.root, self.fdir)]
        self.assertTrue(any('brief confirm' in t for t in acts))
        self.assertTrue(any('--queue-dir .local/queue/full add .local/tasks/g/g-foo' in t for t in acts))

    def test_old_claim_is_listed_for_release(self):
        flow.log_event(self.fdir, 'session-start')
        wq.claim(self.q, 'haiku-2', t=1000.0)
        acts = [t for _, t in flow.next_actions(self.root, self.fdir, now=1000.0 + flow.CLAIM_LOOK_SECONDS + 60)]
        self.assertTrue(any('release .local/tasks/g/g-foo' in t and 'haiku-2' in t for t in acts), acts)
        acts = [t for _, t in flow.next_actions(self.root, self.fdir, now=1060.0)]
        self.assertTrue(any('haiku-2 works .local/tasks/g/g-foo' in t for t in acts), acts)

    def test_briefs_are_written_under_local_briefs(self):
        paths = flow.brief_drafter(self.root, self.fdir, 'cheap', 2)
        self.assertEqual(len(paths), 2)
        for p in paths:
            text = (self.root / p).read_text()
            self.assertIn('docs/drafter-runbook.md', text)
            self.assertIn('Do not push, post publicly, mark `matched`, or start further agents.', text)
        self.assertTrue((self.root / flow.brief_direction(self.root, self.fdir)).is_file())

    def test_friction_and_direction_due(self):
        flow.log_event(self.fdir, 'session-start')
        acts = flow.next_actions(self.root, self.fdir)
        self.assertTrue(any('friction.py --write' in t for _, t in acts))
        self.assertTrue(any(k == 'end' and 'brief direction' in t for k, t in acts))
        flow.log_event(self.fdir, 'friction')
        flow.log_event(self.fdir, 'integrated', accepted=flow.DIRECTION_EVERY)
        acts = flow.next_actions(self.root, self.fdir)
        self.assertFalse(any('friction.py' in t for _, t in acts))
        self.assertTrue(any(k == 'run' and 'brief direction' in t for k, t in acts))


class Cli(unittest.TestCase):
    def test_help_and_status_on_empty_flow_dir(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            out = subprocess.run([sys.executable, str(ROOT / 'tools/flow.py'), '--offline', '--flow-dir', str(tmp), 'status'],
                                 cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, SKYRIM_QUEUE_DIR=str(tmp)))
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn('state counts', out.stdout)
        finally:
            shutil.rmtree(tmp)


if __name__ == '__main__':
    unittest.main()
