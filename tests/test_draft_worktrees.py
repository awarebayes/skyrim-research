"""Synthetic repository tests for draft isolation, harvest refusal and immutable transport."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import draft_worktrees as drafts
import work_queue as wq
import flow
import lint_reconstruction as lint
import synthetic_pecoff as fx
from source_digest import include_closure, tu_digest
from test_flow import Repo, BUILD, git


class DraftWorktrees(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.repo = Repo(self.tmp)
        self.root = self.repo.root
        self.q = self.root / '.local/queue/mid'
        self.q.mkdir(parents=True)
        self.unit = {'dir': '.local/tasks/g/g-foo', 'key': 'g-foo',
                     'sources': ['reconstruction/x/Foo.h', 'reconstruction/x/Foo.cpp'],
                     'functions': ['0x1000', '0x1010'], 'budget': 3}
        (self.q / 'queue.tsv').write_text('\t'.join((self.unit['dir'], ','.join(self.unit['sources']),
                                                    ','.join(self.unit['functions']), '3')) + '\n')
        self.directory = self.root / self.unit['dir']
        self.directory.mkdir(parents=True)
        drafts.save(self.directory / 'task.json', {
            'compiled': self.unit['sources'][-1], 'build_id': BUILD, 'max_attempts': 3,
            'functions': [{'rva': '0x1000', 'size': 16, 'symbol': fx.FUNCTION},
                          {'rva': '0x1010', 'size': 8, 'symbol': 'FailedAddition'}]})
        drafts.save(self.directory / 'symbols.json', {'symbols': {}})
        self.claims = patch('claims.project_claims', return_value=({}, None))
        self.claims.start()
        self.addCleanup(self.claims.stop)
        # Minimal transport fixtures omit source paperwork; helper-policy tests use real lint.
        self.lint_patch = patch.object(lint, 'lint_tree', return_value=[])
        self.lint_patch.start()
        self.addCleanup(self.lint_patch.stop)
        self.object_bytes = fx.coff_object()
        self.preparation = patch.object(drafts, 'prepare_regressions')
        self.preparation.start()
        self.addCleanup(self.preparation.stop)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def claim(self, tier='first'):
        return wq.claim(self.q, 'worker-' + tier, profile='claude-low', tier=tier)

    def clean_attempt(self, command, cwd=None, **kwargs):
        if str(command[1]).endswith('/tools/verifier/attempt'):
            directory = Path(command[2])
            task = drafts.read(directory / 'task.json')
            dest = directory / 'attempts/001'
            dest.mkdir(parents=True)
            digest = tu_digest(cwd, include_closure(cwd, task['compiled']))
            drafts.save(dest / 'result.json', {'source_revision': digest})
            (dest / 'candidate.obj').write_bytes(self.object_bytes)
            for fn in task['functions']:
                drafts.save(dest / f'0x{int(str(fn["rva"]), 0):x}/report.json', {'result': 'pass'})
            return subprocess.CompletedProcess(command, 0, 'all pass\n', '')
        return self.real_run(command, cwd=cwd, **kwargs)

    def finish(self, tier='first', passed=True):
        records = [json.dumps({'rva': '0x1000', 'result': 'pass' if passed else 'fail'}),
                   json.dumps({'rva': '0x1010', 'result': 'fail'}), json.dumps({'unit': 'Foo'})]
        self.real_run = subprocess.run
        with patch('draft_worktrees.subprocess.run', side_effect=self.clean_attempt):
            return wq.finish(self.q, self.unit['dir'], records, tier=tier)

    def test_claim_is_private_labelled_and_resumes_without_changing_shared_source(self):
        src = self.root / self.unit['sources'][-1]
        src.write_text('shared unfinished work\n')
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        self.assertEqual((tree / self.unit['sources'][-1]).read_text(), 'int a;\n')
        self.assertEqual((tree / '.local/tasks').resolve(), (self.root / '.local/tasks').resolve())
        self.assertEqual(drafts.read(tree / '.local/worktree-owner.json')['task'], 'g-foo')
        self.assertEqual(self.claim()['draft'], unit['draft'])
        with self.assertRaisesRegex(ValueError, 'claimed draft checkout'):
            drafts.route_attempt(self.directory, self.root)
        drafts.route_attempt(self.directory, tree)
        with self.assertRaisesRegex(ValueError, 'clean harvested snapshot'):
            drafts.harvest_for_confirmation(self.directory)
        self.assertEqual(src.read_text(), 'shared unfinished work\n')

    def test_harvest_commits_only_unit_and_carries_snapshot_to_later_tier(self):
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('int harvested;\n')
        self.finish()
        harvest = drafts.current(self.root, self.unit)
        self.assertEqual(harvest['passing'], [0x1000])
        self.assertEqual(git(tree, 'diff-tree', '--no-commit-id', '--name-only', '-r', harvest['commit']),
                         self.unit['sources'][-1])
        (tree / self.unit['sources'][-1]).write_text('int later_dirty;\n')
        fallback = self.claim('fallback')
        other = Path(fallback['draft']['tree'])
        self.assertEqual((other / self.unit['sources'][-1]).read_text(), 'int harvested;\n')
        self.assertEqual(git(other, 'rev-parse', 'HEAD'), git(self.root, 'rev-parse', 'origin/main'))
        self.assertEqual(drafts.read(Path(harvest['task']) / 'task.json')['functions'][0]['rva'], '0x1000')

    def test_clean_attempt_failure_has_no_harvest_or_done_marker(self):
        self.claim()
        with patch('draft_worktrees.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'failed')):
            with self.assertRaisesRegex(wq.QueueError, 'clean harvest attempt failed'):
                wq.finish(self.q, self.unit['dir'], ['{"rva":"0x1000","result":"pass"}'])
        self.assertIsNone(drafts.current(self.root, self.unit))
        self.assertFalse((self.q / 'done/g-foo.json').exists())
        self.assertTrue((self.q / 'claims/g-foo.lock').exists())
        self.assertTrue((self.directory / 'harvest-error-first.json').exists())
        hold = drafts.read(self.q / 'holds/g-foo.json')
        self.assertEqual(hold['kind'], 'harvest-refusal')
        self.assertIn('clean harvest attempt failed', hold['reason'])
        self.assertIsNone(self.claim())
        self.finish()
        self.assertFalse((self.q / 'holds/g-foo.json').exists())

    def test_standalone_prepared_skeleton_replaces_an_unrelated_base_stub(self):
        task = drafts.read(self.directory / 'task.json')
        task['export'] = {'unit_already_records': []}
        drafts.save(self.directory / 'task.json', task)
        for rel in self.unit['sources']:
            path = self.directory / 'skeleton' / Path(rel).name
            path.parent.mkdir(exist_ok=True)
            path.write_text('// prepared ' + Path(rel).name + '\n')
        tree = Path(self.claim()['draft']['tree'])
        self.assertEqual((tree / self.unit['sources'][-1]).read_text(), '// prepared Foo.cpp\n')
        self.assertEqual((self.root / self.unit['sources'][-1]).read_text(), 'int a;\n')

    def test_standalone_without_cached_skeleton_regenerates_over_base_stub(self):
        task = drafts.read(self.directory / 'task.json')
        task['export'] = {'unit_already_records': []}
        drafts.save(self.directory / 'task.json', task)
        import unit_skeleton
        with patch.object(unit_skeleton, 'skeleton_files', return_value=(
                self.unit['sources'][0], '// prepared header\n', self.unit['sources'][1], '// prepared source\n')):
            tree = Path(self.claim()['draft']['tree'])
        self.assertEqual((tree / self.unit['sources'][0]).read_text(), '// prepared header\n')
        self.assertEqual((tree / self.unit['sources'][1]).read_text(), '// prepared source\n')

    def test_resume_repairs_an_untouched_base_stub_but_preserves_drafter_edits(self):
        tree = Path(self.claim()['draft']['tree'])
        task = drafts.read(self.directory / 'task.json')
        task['export'] = {'unit_already_records': []}
        drafts.save(self.directory / 'task.json', task)
        import unit_skeleton
        with patch.object(unit_skeleton, 'skeleton_files', return_value=(
                self.unit['sources'][0], '// prepared header\n', self.unit['sources'][1], '// prepared source\n')):
            self.claim()
        self.assertEqual((tree / self.unit['sources'][1]).read_text(), '// prepared source\n')
        (tree / self.unit['sources'][1]).write_text('// current draft\n')
        self.claim()
        self.assertEqual((tree / self.unit['sources'][1]).read_text(), '// current draft\n')

    def test_preparation_checks_the_recipe_and_runs_all_accepted_regressions(self):
        import hashlib
        self.preparation.stop()
        recipe = self.root / 'reconstruction/recipes/r.json'
        drafts.save(recipe, {'flags': ['/O2']})
        task = drafts.read(self.directory / 'task.json')
        task['recipe'] = recipe.relative_to(self.root).as_posix()
        drafts.save(self.directory / 'task.json', task)
        data = drafts.read(self.root / 'data/progress.json')
        for fn in data['functions']:
            fn['status'] = 'matched'
            rec_path = self.root / fn['report']
            rec = drafts.read(rec_path)
            rec['recipe'] = {'path': task['recipe'], 'sha256': hashlib.sha256(recipe.read_bytes()).hexdigest()}
            rec['runs'][0]['report'] = {'function': {'rva': hex(fn['rva']), 'size': fn['size'],
                                                    'symbol': fx.FUNCTION}}
            drafts.save(rec_path, rec)
        drafts.save(self.root / 'data/progress.json', data)
        self.real_run = subprocess.run
        with patch('draft_worktrees.subprocess.run', side_effect=self.clean_attempt):
            drafts.prepare_regressions(self.root, self.unit, self.root)
        self.assertEqual(drafts.read(self.directory / 'preparation.json')['passing'], [0x1000, 0x1010])
        with patch('draft_worktrees.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'fail')):
            with self.assertRaisesRegex(ValueError, 'accepted regressions do not pass'):
                drafts.prepare_regressions(self.root, self.unit, self.root)
        recipe.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'not the task recipe'):
            drafts.prepare_regressions(self.root, self.unit, self.root)

    def legacy_pass(self):
        data = drafts.read(self.root / 'data/progress.json')
        data['functions'][0]['status'] = 'mapped'
        drafts.save(self.root / 'data/progress.json', data)
        git(self.root, 'add', 'data/progress.json')
        (self.q / 'results.jsonl').write_text(json.dumps({
            'queue_unit': self.unit['dir'], 'tier': 'first', 'rva': '0x1000', 'result': 'pass'}) + '\n')

    def test_legacy_earlier_pass_is_carried_without_a_harvest(self):
        self.legacy_pass()
        (self.root / self.unit['sources'][-1]).write_text('int a;\nint earlier;\n')
        state = drafts.create(self.root, self.unit, 'strong', 'worker-strong')
        self.assertEqual((Path(state['tree']) / self.unit['sources'][-1]).read_text(),
                         'int a;\nint earlier;\n')
        self.assertEqual(state['carryover']['passing'], [0x1000])

    def test_recover_existing_tier_keeps_its_work_and_earlier_pass(self):
        self.legacy_pass()
        state = drafts.create(self.root, self.unit, 'strong', 'worker-strong')
        tree = Path(state['tree'])
        (tree / self.unit['sources'][0]).write_text('#pragma once\nint strong;\n')
        (self.root / self.unit['sources'][-1]).write_text('int a;\nint earlier;\n')
        # A checkout made before carry-over support has no completion marker.
        state.pop('carryover', None)
        drafts.save(self.directory / 'draft-strong.json', state)
        drafts.create(self.root, self.unit, 'strong', 'worker-strong')
        self.assertIn('int strong;', (tree / self.unit['sources'][0]).read_text())
        self.assertIn('int earlier;', (tree / self.unit['sources'][-1]).read_text())

    def test_legacy_carryover_conflict_preserves_both_inputs(self):
        self.legacy_pass()
        state = drafts.create(self.root, self.unit, 'strong', 'worker-strong')
        tree = Path(state['tree'])
        state.pop('carryover', None)
        drafts.save(self.directory / 'draft-strong.json', state)
        (tree / self.unit['sources'][-1]).write_text('int strong;\n')
        (self.root / self.unit['sources'][-1]).write_text('int earlier;\n')
        with self.assertRaisesRegex(ValueError, 'preserve both tiers'):
            drafts.create(self.root, self.unit, 'strong', 'worker-strong')
        self.assertEqual((tree / self.unit['sources'][-1]).read_text(), 'int strong;\n')
        self.assertEqual((self.root / self.unit['sources'][-1]).read_text(), 'int earlier;\n')

    def test_setup_link_and_label_failures_roll_back_and_next_claim_recovers(self):
        for stage in ('link_private', 'label'):
            with self.subTest(stage=stage), patch.object(drafts, stage, side_effect=OSError('injected')):
                with self.assertRaisesRegex(wq.QueueError, 'rolled back'):
                    self.claim()
            self.assertFalse((self.q / 'claims/g-foo.lock').exists())
            self.assertFalse((self.directory / 'draft-first.json').exists())
            self.assertEqual(git(self.root, 'branch', '--list', 'draft/*'), '')
        self.assertTrue(Path(self.claim()['draft']['tree']).is_dir())

    def test_interrupted_setup_claim_recovers_without_becoming_a_legacy_claim(self):
        self.q.joinpath('claims').mkdir()
        wq.try_create(self.q / 'claims/g-foo.lock', 'worker-first', wq.now(), 'claude-low')
        tree = self.root / '.local/worktrees/draft/g-foo-first'
        branch = 'draft/g-foo-first'
        drafts.save(self.directory / 'draft-first.json', {'ready': False, 'tree': str(tree), 'branch': branch})
        git(self.root, 'worktree', 'add', '-b', branch, str(tree), 'origin/main')
        unit = self.claim()
        self.assertTrue(unit['draft']['ready'])
        self.assertTrue((tree / '.local/worktree-owner.json').is_file())
        self.assertTrue((tree / '.local/tasks').is_symlink())

    def test_interruption_before_setup_state_is_written_still_creates_private_checkout(self):
        self.q.joinpath('claims').mkdir()
        wq.try_create(self.q / 'claims/g-foo.lock', 'worker-first', wq.now(), 'claude-low')
        self.assertTrue(Path(self.claim()['draft']['tree']).is_dir())

    def test_setup_overlay_failure_rolls_back_private_inputs_and_checkout(self):
        self.claim()
        self.finish()
        before = (self.directory / 'task.json').read_bytes()
        with patch.object(drafts, 'copy_commit', side_effect=ValueError('injected')):
            with self.assertRaisesRegex(wq.QueueError, 'rolled back'):
                self.claim('fallback')
        self.assertEqual((self.directory / 'task.json').read_bytes(), before)
        self.assertFalse((self.directory / 'draft-fallback.json').exists())
        self.assertTrue(Path(self.claim('fallback')['draft']['tree']).is_dir())

    def test_setup_skeleton_failure_rolls_back_and_retry_completes_setup(self):
        git(self.root, 'rm', *self.unit['sources'])
        git(self.root, 'commit', '-m', 'synthetic missing unit')
        git(self.root, 'push', 'origin', 'main')
        import unit_skeleton
        with patch.object(unit_skeleton, 'write_skeleton', side_effect=unit_skeleton.SkeletonError('injected')):
            with self.assertRaisesRegex(wq.QueueError, 'rolled back'):
                self.claim()
        self.assertEqual(git(self.root, 'branch', '--list', 'draft/*'), '')
        self.assertFalse((self.directory / 'draft-first.json').exists())

        def skeleton(directory, repo):
            for name in self.unit['sources']:
                p = repo / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('// synthetic skeleton\n')

        with patch.object(unit_skeleton, 'write_skeleton', side_effect=skeleton):
            unit = self.claim()
        self.assertTrue((Path(unit['draft']['tree']) / self.unit['sources'][-1]).is_file())

    def test_leftover_failed_definition_refuses_harvest(self):
        self.claim()
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, 'FailedAddition': 2}):
            with self.assertRaisesRegex(wq.QueueError, 'remove failed additions'):
                self.finish()
        self.assertIsNone(drafts.current(self.root, self.unit))

    def test_optimized_out_failed_target_body_refuses_harvest(self):
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('int SyntheticSum() { return 0; }\n'
                                                    'static int FailedAddition() { return 1; }\n')
        with self.assertRaisesRegex(wq.QueueError, 'source contains target bodies without passing attempts'):
            self.finish()
        (tree / self.unit['sources'][-1]).write_text('int SyntheticSum() { return 0; }\n')
        self.finish()

    def linted_claim(self):
        self.lint_patch.stop()
        drafts.save(self.root / 'builds/target.json', {'build_id': BUILD})
        drafts.save(self.root / 'reconstruction/recipes/r.json', {})
        (self.root / self.unit['sources'][0]).write_text(
            f'// Foo, build {BUILD}. Source exposure: binary-analysis. Names are GUESS.\n'
            '#pragma once\nclass Foo {};\n')
        source = (f'// SyntheticSum, build {BUILD}, RVA 0x1000, 16 bytes.\n'
                  f'// Evidence: reports/{BUILD}/0x1000.json\n'
                  '// Source exposure: binary-analysis. Drafted by a synthetic test.\n'
                  '// Recipe: reconstruction/recipes/r.json\n#include "Foo.h"\n')
        (self.root / self.unit['sources'][-1]).write_text(source + 'int SyntheticSum() { return 0; }\n')
        git(self.root, 'add', 'builds/target.json', 'reconstruction/recipes/r.json', *self.unit['sources'])
        git(self.root, 'commit', '-m', 'synthetic lint inputs')
        git(self.root, 'push', 'origin', 'main')
        unit = self.claim()
        return Path(unit['draft']['tree']), source

    def test_scope_guard_ctor_dtor_used_by_pass_are_harvested_under_existing_lint(self):
        tree, source = self.linted_claim()
        ctor, dtor = '??0Scope@@QEAA@XZ', '??1Scope@@QEAA@XZ'
        source += ('struct Scope { int& slot; int saved;\n'
                   ' Scope(int& s) : slot(s), saved(s) { slot = 1; }\n'
                   ' ~Scope() { slot = saved; } };\n'
                   'int slot;\nint SyntheticSum() { Scope scope(slot); return slot; }\n')
        (tree / self.unit['sources'][-1]).write_text(source)
        obj = fx.Unit()
        for symbol in (fx.FUNCTION, ctor, dtor):
            section = obj.section('.text$mn', fx.CALLEE_CODE, fx.SCN_CODE)
            obj.define(symbol, section, storage=2, function=True)
        self.object_bytes = obj.coff()
        # A reference binding outside the task/inventory function targets does not make this
        # helper a separately compared function. Its actual uses still face the comparator.
        drafts.save(self.directory / 'symbols.json', {'symbols': {dtor: {'rva': 0x9000}}})
        self.assertEqual(lint.lint_tree(tree, self.unit['sources']), [])
        self.finish()
        self.assertIsNotNone(drafts.current(self.root, self.unit))

    def test_unreferenced_helper_follows_existing_lint_without_new_harvest_rule(self):
        tree, source = self.linted_claim()
        source += ('inline int UnusedHelper() { return 7; }\n'
                   'int SyntheticSum() { return 0; }\n')
        (tree / self.unit['sources'][-1]).write_text(source)
        # Existing lint has no unused-helper rule; review still judges dead code and rationale.
        self.assertEqual(lint.lint_tree(tree, self.unit['sources']), [])
        self.finish()

    def test_helper_lint_finding_is_not_suppressed_by_harvest(self):
        tree, source = self.linted_claim()
        source += ('__forceinline int UnusedHelper() { return 7; }\n'
                   'int SyntheticSum() { return 0; }\n')
        (tree / self.unit['sources'][-1]).write_text(source)
        findings = lint.lint_tree(tree, self.unit['sources'])
        self.assertTrue(any('__forceinline' in finding for finding in findings))
        with self.assertRaisesRegex(wq.QueueError, 'harvest lint failed'):
            self.finish()
        self.assertIsNone(drafts.current(self.root, self.unit))

    def test_definition_bound_to_other_inventory_target_is_not_a_helper(self):
        self.claim()
        drafts.save(self.directory / 'symbols.json', {'symbols': {'InventoryOther': {'rva': 0x2000}}})
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, 'InventoryOther': 2}):
            with self.assertRaisesRegex(wq.QueueError, 'target functions without passing attempts'):
                self.finish()

    def existing_header(self):
        symbol = '??_GExisting@@UEAAPEAXI@Z'
        (self.root / self.unit['sources'][0]).write_text('class Existing { public: virtual ~Existing(); };\n')
        (self.root / self.unit['sources'][1]).write_text('#include "Foo.h"\nint a;\n')
        git(self.root, 'add', *self.unit['sources'])
        git(self.root, 'commit', '-m', 'synthetic pre-existing stand-in')
        git(self.root, 'push', 'origin', 'main')
        drafts.save(self.directory / 'symbols.json', {'symbols': {symbol: {'rva': 0x2000}}})
        return symbol

    def test_untouched_header_emitted_destructor_is_not_a_failed_addition(self):
        symbol = self.existing_header()
        self.claim()
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, symbol: 2}):
            self.finish()

    def test_unchanged_standin_class_survives_unrelated_header_addition(self):
        symbol = self.existing_header()
        tree = Path(self.claim()['draft']['tree'])
        header = tree / self.unit['sources'][0]
        header.write_text(header.read_text() + 'int NewDeclaration();\n')
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, symbol: 2}):
            self.finish()

    def test_preexisting_inventory_body_is_not_a_new_candidate_when_cpp_is_extended(self):
        source = self.root / self.unit['sources'][-1]
        source.write_text('int InventoryOther() { return 1; }\n')
        git(self.root, 'add', self.unit['sources'][-1])
        git(self.root, 'commit', '-m', 'synthetic existing uncompared body')
        git(self.root, 'push', 'origin', 'main')
        drafts.save(self.directory / 'symbols.json', {'symbols': {'InventoryOther': {'rva': 0x2000}}})
        tree = Path(self.claim()['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text(source.read_text() + 'int NewHelper() { return 2; }\n')
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, 'InventoryOther': 2}):
            self.finish()

    def test_added_inventory_target_body_cannot_use_existing_header_exemption(self):
        symbol = self.existing_header()
        tree = Path(self.claim()['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('#include "Foo.h"\nExisting::~Existing() {}\n')
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, symbol: 2}):
            with self.assertRaisesRegex(wq.QueueError, 'target functions without passing attempts'):
                self.finish()

    def test_unit_target_in_untouched_header_still_requires_a_pass(self):
        symbol = self.existing_header()
        task = drafts.read(self.directory / 'task.json')
        task['functions'][1]['symbol'] = symbol
        drafts.save(self.directory / 'task.json', task)
        self.claim()
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, symbol: 2}):
            with self.assertRaisesRegex(wq.QueueError, 'target functions without passing attempts'):
                self.finish()

    def test_added_defaulted_destructor_is_not_an_untouched_header_emission(self):
        symbol = self.existing_header()
        tree = Path(self.claim()['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('#include "Foo.h"\nExisting::~Existing() noexcept(true) = default;\n')
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, symbol: 2}):
            with self.assertRaisesRegex(wq.QueueError, 'target functions without passing attempts'):
                self.finish()

    def test_harvest_does_not_add_an_unrelated_inventory_stub_to_the_task(self):
        self.claim()
        data = drafts.read(self.root / 'data/progress.json')
        row = dict(data['functions'][-1], rva=0x1020, id=f'{BUILD}-0x1020', status='matched',
                   report=f'reports/{BUILD}/0x1020.json')
        data['functions'].append(row)
        drafts.save(self.root / 'data/progress.json', data)
        drafts.save(self.root / row['report'], {'source': {'compiled': self.unit['sources'][-1]},
            'runs': [{'report': {'function': {'rva': '0x1020', 'size': 3, 'symbol': 'UnrelatedStub'}}}]})
        self.finish()
        clean = drafts.read(Path(drafts.current(self.root, self.unit)['task']) / 'task.json')
        self.assertEqual([f['rva'] for f in clean['functions']], ['0x1000'])

    def test_qualified_target_hint_does_not_turn_a_failed_candidate_into_a_helper(self):
        self.claim()
        drafts.save(self.directory / 'bind-hints.json', {'Other::Failed': '0x1010'})
        sys.path.insert(0, str(ROOT / 'tools/verifier'))
        import bind
        failed = '?Failed@Other@@YAHXZ'
        with patch.object(bind, 'defined_functions', return_value={fx.FUNCTION: 1, failed: 2}):
            with self.assertRaisesRegex(wq.QueueError, 'target functions without passing attempts'):
                self.finish()

    def test_emitted_helper_reference_keeps_comparator_unbound_symbol_refusal(self):
        from compare import compare
        unit = fx.Unit()
        body = unit.section('.text$mn', fx.CODE, fx.SCN_CODE)
        unit.define(fx.FUNCTION, body, storage=2, function=True)
        helper = unit.section('.text$mn', fx.CALLEE_CODE, fx.SCN_CODE)
        unit.define(fx.CALLEE, helper, storage=2, function=True)
        for offset, symbol, kind in fx.RELOCS:
            if symbol != fx.CALLEE:
                unit.external(symbol)
            unit.reloc(body, offset, symbol, kind)
        args = fx.unit_inputs(unit, fx.FUNCTION, {fx.BASE: 0x3100, fx.COUNTER: 0x3104})
        report = compare(**args)
        self.assertEqual((report['result'], report['reason']), ('fail', 'unresolved-symbol'))

    def test_final_failure_removes_worktrees_and_branches_keeps_near_misses(self):
        self.claim()
        self.finish(passed=False)
        self.claim('fallback')
        wq.finish(self.q, self.unit['dir'], ['{"rva":"0x1000","result":"fail"}',
                                            '{"rva":"0x1010","result":"fail"}'], tier='fallback')
        unit = self.claim('strong')
        near = self.directory / 'near-miss/0x1000.cpp'
        near.parent.mkdir()
        near.write_text('// synthetic near miss\n')
        wq.finish(self.q, self.unit['dir'], ['{"rva":"0x1000","result":"fail"}',
                                            '{"rva":"0x1010","result":"fail"}'], tier='strong')
        self.assertFalse(Path(unit['draft']['tree']).exists())
        self.assertEqual(git(self.root, 'branch', '--list', 'draft/*'), '')
        self.assertTrue(near.is_file())
        with self.assertRaisesRegex(ValueError, 'no live checkout'):
            drafts.route_attempt(self.directory, self.root)
        with self.assertRaisesRegex(ValueError, 'clean harvested snapshot'):
            drafts.harvest_for_confirmation(self.directory)

    def test_final_failure_after_prior_pass_preserves_harvest_but_removes_draft_branches(self):
        self.claim()
        self.finish()
        for tier in ('fallback', 'strong'):
            self.claim(tier)
            self.real_run = subprocess.run
            with patch('draft_worktrees.subprocess.run', side_effect=self.clean_attempt):
                wq.finish(self.q, self.unit['dir'], ['{"rva":"0x1010","result":"fail"}'], tier=tier)
        harvest = drafts.current(self.root, self.unit)
        self.assertFalse(Path(harvest['tree']).exists())
        self.assertEqual(git(self.root, 'branch', '--list', 'draft/*'), '')
        self.assertEqual(git(self.root, 'rev-parse', 'refs/harvests/g-foo/strong'), harvest['commit'])
        self.assertTrue((Path(harvest['attempt']) / 'candidate.obj').is_file())

    def test_integration_and_state_use_harvest_even_after_working_trees_change(self):
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('int harvested;\n')
        self.finish()
        harvest = drafts.current(self.root, self.unit)
        rec_path = self.root / f'reports/{BUILD}/0x1000.json'
        rec = drafts.read(rec_path)
        rec['source']['digest'] = harvest['digest']
        rec['source']['translation_unit'] = harvest['sources']
        drafts.save(rec_path, rec)
        (tree / self.unit['sources'][-1]).write_text('int dirty_draft;\n')
        (self.root / self.unit['sources'][-1]).write_text('int dirty_shared;\n')
        fn = flow.inventory(self.root)['functions'][0]
        self.assertEqual(flow.record_state(self.root, fn), 'confirmed')
        made = flow.review_group(self.root, self.repo.fdir, select={fn['id']})
        group = flow.load_group(self.repo.fdir, made[0])
        frozen = Path(group['review_root'])
        self.assertEqual((frozen / self.unit['sources'][-1]).read_text(), 'int harvested;\n')
        brief = self.root / group['brief']
        self.assertIn(str(frozen), brief.read_text())
        rerun = self.root / '.local/briefs' / f'rerun-{group["name"]}.md'
        self.assertIn(harvest['task'], rerun.read_text())
        dest = self.tmp / 'integration'
        git(self.root, 'worktree', 'add', '--detach', str(dest), 'origin/main')
        flow.carry_into_tree(self.root, dest, ['0x1000'], {'0x1000': fn})
        self.assertEqual((dest / self.unit['sources'][-1]).read_text(), 'int harvested;\n')
        # Integration cleanup requires accepted origin state and exactly the harvested digest.
        data = flow.inventory(dest)
        data['functions'][0]['status'] = 'matched'
        drafts.save(dest / 'data/progress.json', data)
        git(dest, 'add', 'data/progress.json', *self.unit['sources'])
        git(dest, 'commit', '-m', 'synthetic integration')
        git(dest, 'push', 'origin', 'HEAD:main')
        active = self.q / 'claims-fallback/g-foo.lock'
        active.parent.mkdir()
        wq.try_create(active, 'next-tier', wq.now(), 'claude-low', 'fallback')
        drafts.cleanup_integrated(self.root)
        self.assertTrue(tree.exists())
        active.unlink()
        drafts.cleanup_integrated(self.root)
        self.assertFalse(tree.exists())
        self.assertTrue(drafts.current(self.root, self.unit)['integrated'])

    def test_confirm_reads_commit_and_not_mutable_draft(self):
        data = drafts.read(self.root / 'data/progress.json')
        later_enrollment = data['functions'].pop(0)
        drafts.save(self.root / 'data/progress.json', data)
        git(self.root, 'add', 'data/progress.json')
        git(self.root, 'commit', '-m', 'synthetic source precedes enrollment')
        git(self.root, 'push', 'origin', 'main')
        unit = self.claim()
        tree = Path(unit['draft']['tree'])
        (tree / self.unit['sources'][-1]).write_text('int harvested;\n')
        self.finish()
        data['functions'].append(later_enrollment)
        drafts.save(self.root / 'data/progress.json', data)
        (tree / self.unit['sources'][-1]).write_text('int dirty_draft;\n')
        self.real_run = subprocess.run
        seen = []

        def run(command, cwd=None, **kwargs):
            if len(command) > 1 and ('verifier/bind.py' in str(command[1]) or 'verifier/confirm' in str(command[1])):
                seen.append((Path(cwd) / self.unit['sources'][-1]).read_text())
                self.assertIn(later_enrollment, drafts.read(Path(cwd) / 'data/progress.json')['functions'])
                return subprocess.CompletedProcess(command, 0)
            return self.real_run(command, cwd=cwd, **kwargs)

        with patch('draft_worktrees.subprocess.run', side_effect=run):
            self.assertEqual(drafts.confirm_one(self.root, self.directory, ['--out', str(self.tmp / 'out')]), 0)
        self.assertEqual(seen, ['int harvested;\n', 'int harvested;\n'])

    def test_private_diagnostics_keep_shared_host_slots(self):
        shared = self.root / '.local/verifier'
        (shared / 'runner-slots').mkdir(parents=True)
        drafts.save(shared / 'config.json', {})
        unit = self.claim()
        verifier = Path(unit['draft']['tree']) / '.local/verifier'
        self.assertFalse(verifier.is_symlink())
        self.assertEqual((verifier / 'runner-slots').resolve(), (shared / 'runner-slots').resolve())
        self.assertEqual((verifier / 'config.json').resolve(), (shared / 'config.json').resolve())
        (verifier / 'diagnostics').mkdir()
        self.assertTrue((verifier / 'diagnostics').resolve().is_relative_to(Path(unit['draft']['tree'])))

    def test_confirm_cannot_invent_or_change_an_enrolled_identity(self):
        self.claim()
        self.finish()
        data = drafts.read(self.root / 'data/progress.json')
        data['functions'][0]['size'] += 1
        drafts.save(self.root / 'data/progress.json', data)
        with self.assertRaisesRegex(ValueError, 'must be enrolled'):
            drafts.confirm_one(self.root, self.directory, [])
        data['functions'].pop(0)
        drafts.save(self.root / 'data/progress.json', data)
        with self.assertRaisesRegex(ValueError, 'must be enrolled'):
            drafts.confirm_one(self.root, self.directory, [])


if __name__ == '__main__':
    unittest.main()
