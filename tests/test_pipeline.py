"""Tests for the local parts of tools/verifier/attempt and confirm (no Boat machine involved)."""
import base64
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
import disasm  # noqa: E402
import pipeline  # noqa: E402
from importlib.machinery import SourceFileLoader  # noqa: E402
import importlib.util  # noqa: E402


def load_script(name):
    loader = SourceFileLoader(name, str(ROOT / 'tools' / 'verifier' / name))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

TARGET = json.loads((ROOT / 'builds/target.json').read_text())


class TaskFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.task_dir = self.tmp / '.local' / 'tasks' / 'demo-task'
        self.task_dir.mkdir(parents=True)
        (self.task_dir / 'symbols.json').write_text('{}')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, **overrides):
        task = {'build_id': TARGET['build_id'], 'compiled': 'reconstruction/inventory/ArmorRatingVisitor.cpp',
                'recipe_name': 'msvc-19.16.27054-o2',
                'functions': [{'rva': '0x73ad90', 'size': 84, 'symbol': '?F@@YAXXZ'}]}
        task.update(overrides)
        (self.task_dir / 'task.json').write_text(json.dumps(task))

    def test_minimal_task(self):
        self.write()
        task = pipeline.load_task(self.task_dir)
        self.assertEqual(task['task_id'], 'demo-task')
        self.assertEqual(task['recipe'], 'reconstruction/recipes/msvc-19.16.27054-o2.json')
        self.assertEqual(task['functions'], [{'rva': 0x73ad90, 'size': 84, 'symbol': '?F@@YAXXZ'}])
        self.assertIsNone(task['symbols_repo'])
        files, closure = pipeline.unit_manifest(task)
        self.assertEqual(closure, ['reconstruction/inventory/ArmorRatingVisitor.cpp',
                                   'reconstruction/inventory/ArmorRatingVisitor.h'])
        self.assertEqual(files[pipeline.PRIVATE_SYMBOLS], self.task_dir / 'symbols.json')
        for name in pipeline.TOOL_FILES:
            self.assertIn(name, files)
        self.assertFalse(any(name.startswith(('.local', 'data/', 'findings/')) for name in files))

    def test_public_symbol_map_is_a_repository_path(self):
        self.write(symbols='reports/sse-steam-1-7-104/symbol-map.json')
        task = pipeline.load_task(self.task_dir)
        self.assertEqual(task['symbols_repo'], 'reports/sse-steam-1-7-104/symbol-map.json')
        self.assertEqual(task['symbols_local'], ROOT / 'reports/sse-steam-1-7-104/symbol-map.json')

    def test_invalid_tasks_are_refused(self):
        for overrides in ({'build_id': 'other-build'}, {'task_id': 'has_underscore'},
                          {'compiled': 'src/x.cpp'}, {'recipe_name': None, 'recipe': '/tmp/r.json'},
                          {'functions': []}, {'functions': [{'rva': 'zz', 'size': 1, 'symbol': 'a'}]},
                          {'functions': [{'rva': 1, 'size': 1, 'symbol': 'a'}, {'rva': 1, 'size': 2, 'symbol': 'b'}]},
                          {'symbols': 'missing.json'}, {'record_notes': 'not a list'}):
            with self.subTest(overrides=overrides):
                self.write(**overrides)
                with self.assertRaises(pipeline.PipelineError):
                    pipeline.load_task(self.task_dir)

    def test_task_dir_must_be_private(self):
        public = self.tmp / 'tasks' / 'x'
        public.mkdir(parents=True)
        with self.assertRaises(pipeline.PipelineError):
            pipeline.load_task(public)

    def test_relative_task_dir_falls_back_to_the_main_checkout(self):
        self.assertEqual(pipeline.resolve_task_dir(self.task_dir), self.task_dir)
        self.assertEqual(pipeline.resolve_task_dir('.local/tasks/not-here'),
                         (pipeline.main_checkout() / '.local/tasks/not-here').resolve())

    def test_confirm_build_block_states_what_ran(self):
        confirm = load_script('confirm')
        task = {'compiled': 'reconstruction/x/A.cpp', 'functions': [{'rva': 0x10}, {'rva': 0x20}]}
        recipe_flags = ['/nologo', '/c', '/O2']
        host = self.tmp / 'host'
        env = {'cleared': ['INCLUDE', 'LIB', 'LIBPATH', 'CL', '_CL_', 'EXTERNAL_INCLUDE'],
               'added_flags': ['/showIncludes'],
               'show_includes': {'repository_files': ['reconstruction/x/A.cpp', 'reconstruction/x/A.h'],
                                 'equals_closure': True}}
        for rva in ('0x10', '0x20'):
            (host / rva).mkdir(parents=True)
            (host / rva / 'build-record.json').write_text(json.dumps({'object_sha256': 'a' * 64, 'environment': env}))
        (host / 'compile-command.json').write_text(json.dumps(
            recipe_flags + ['/showIncludes', '/Fo/w/candidate.obj', 'reconstruction/x/A.cpp']))
        block = confirm.build_block(task, {'h': host})
        self.assertIn('self-reported', block['claim'])
        self.assertEqual(block['hosts']['h']['command_flags'], recipe_flags + ['/showIncludes'])
        self.assertEqual(block['hosts']['h']['object_sha256'], 'a' * 64)
        env['cleared'] = ['INCLUDE']
        (host / '0x10' / 'build-record.json').write_text(json.dumps({'object_sha256': 'a' * 64, 'environment': env}))
        (host / '0x20' / 'build-record.json').write_text(json.dumps({'object_sha256': 'a' * 64, 'environment': env}))
        with self.assertRaises(pipeline.PipelineError):
            confirm.build_block(task, {'h': host})
        recipe = {'flags': recipe_flags, 'compiler': {'version': '19.16.27054 x'}}
        line = confirm.reproduction(dict(task, build_id='b', recipe='r.json', symbols_repo='m.json'),
                                    {'rva': 0x10, 'symbol': '?f@@YAXXZ'}, ['reconstruction/x/A.cpp'], recipe)
        self.assertIn('env -u CL -u EXTERNAL_INCLUDE -u INCLUDE -u LIB -u LIBPATH -u _CL_', line)
        self.assertIn('/O2 /showIncludes /Fo<work>/candidate.obj reconstruction/x/A.cpp', line)

    def test_changed_files(self):
        files = {'a': '1', 'b': '2'}
        self.assertEqual(pipeline.changed_files(files, None, 'm', '/r'), ['a', 'b'])
        state = {'machine': 'm', 'remote_dir': '/r', 'files': {'a': '1', 'b': 'old'}}
        self.assertEqual(pipeline.changed_files(files, state, 'm', '/r'), ['b'])
        self.assertEqual(pipeline.changed_files(files, state, 'other', '/r'), ['a', 'b'])

    def test_remote_script_carries_spec_and_no_local_paths(self):
        self.write()
        task = pipeline.load_task(self.task_dir)
        files, _ = pipeline.unit_manifest(task)
        spec = pipeline.unit_spec(task, files, 'standing')
        script = pipeline.remote_script('/home/user/tasks/demo-task', spec, 'standing',
                                        pipeline.remote_image(task['build_id']), fresh=True)
        self.assertNotIn(str(ROOT), script)
        self.assertNotIn(str(self.tmp), script)
        self.assertIn('rm -rf repo work', script)
        self.assertIn('/home/user/private/sse-steam-1-7-104/SkyrimSE.exe', script)
        blob = script.split('printf %s ')[1].split(' ')[0]
        self.assertEqual(json.loads(base64.b64decode(blob))['files'], spec['files'])


class SideBySide(unittest.TestCase):
    def test_parse_and_mark_differences(self):
        target = disasm.parse('  140001000: 48 83 ec 28    sub rsp, 0x28\n  140001004: c3    ret\n', 0x140001000)
        candidate = disasm.parse('       0: 48 83 ec 28    sub rsp, 0x28\n'
                                 '       4: e8 00 00 00 00    call 0x9\n'
                                 '      0000000000000005:  IMAGE_REL_AMD64_REL32  F\n', 0)
        self.assertEqual(target[1][:2], [4, 'c3'])
        self.assertIn('<REL32 F>', candidate[1][2])
        text = disasm.side_by_side(target, candidate)
        self.assertIn('first differing row 1', text.splitlines()[0])
        self.assertTrue(text.splitlines()[4].startswith('*'))
        self.assertTrue(text.splitlines()[3].startswith(' '))

    def test_relocation_placeholder_rows_are_not_marked(self):
        target = disasm.parse('  140001000: e8 fb 0f 00 00    call 0x140002000\n'
                              '  140001005: 8b 05 10 00 00 00    mov eax, [rip+0x10]\n', 0x140001000)
        candidate = disasm.parse('       0: e8 00 00 00 00    call 0x5\n'
                                 '      0000000000000001:  IMAGE_REL_AMD64_REL32  F\n'
                                 '       5: 8b 0d 00 00 00 00    mov ecx, [rip]\n'
                                 '      0000000000000007:  IMAGE_REL_AMD64_REL32  G\n', 0)
        lines = disasm.side_by_side(target, candidate).splitlines()
        self.assertTrue(lines[3].startswith(' '), lines[3])
        self.assertTrue(lines[4].startswith('*'), lines[4])
        self.assertIn('first differing row 1', lines[0])

    def test_missing_inputs_give_a_reason(self):
        path, why = disasm.write_side_by_side('/nonexistent/x', None, None, 'x.obj', 'f', 0, 1)
        self.assertIsNone(path)
        self.assertIn('llvm-objdump', why)


class CompilerIncludeRoots(unittest.TestCase):
    """The local check that the compiler, given only the recipe's /I roots, finds every include."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp()).resolve()
        for area in ('a', 'b', 'recipes'):
            (self.repo / 'reconstruction' / area).mkdir(parents=True)
        (self.repo / 'reconstruction/b/B.h').write_text('#pragma once\n')
        self.recipe('plain', ['/nologo', '/c', '/O2'])

    def tearDown(self):
        shutil.rmtree(self.repo)

    def recipe(self, name, flags):
        (self.repo / f'reconstruction/recipes/{name}.json').write_text(json.dumps({'flags': flags}))
        return f'reconstruction/recipes/{name}.json'

    def problem(self, include, recipe='reconstruction/recipes/plain.json'):
        (self.repo / 'reconstruction/a/A.cpp').write_text(f'#include "{include}"\n')
        return pipeline.compiler_include_problem({'compiled': 'reconstruction/a/A.cpp', 'recipe': recipe}, self.repo)

    def test_root_relative_include_is_refused_without_a_root(self):
        # The closure accepts it through INCLUDE_ROOTS, so only this check stops the C1083 upload.
        import source_digest
        (self.repo / 'reconstruction/a/A.cpp').write_text('#include "b/B.h"\n')
        self.assertIn('reconstruction/b/B.h', source_digest.include_closure(self.repo, 'reconstruction/a/A.cpp'))
        problem = self.problem('b/B.h')
        self.assertIsNotNone(problem)
        self.assertIn('"../<area>/<Class>.h"', problem)

    def test_relative_includes_pass(self):
        self.assertIsNone(self.problem('../b/B.h'))
        (self.repo / 'reconstruction/a/S.h').write_text('#pragma once\n')
        self.assertIsNone(self.problem('S.h'))

    def test_a_recipe_root_is_honoured(self):
        for flags in (['/I', 'reconstruction'], ['/Ireconstruction'], ['-I', 'reconstruction']):
            with self.subTest(flags=flags):
                self.assertIsNone(self.problem('b/B.h', self.recipe('rooted', ['/c'] + flags)))

    def test_recipe_include_roots(self):
        self.assertEqual(pipeline.recipe_include_roots(['/c', '/I', 'x', '-Iy', '/O2']), ('x', 'y'))
        self.assertEqual(pipeline.recipe_include_roots(['/nologo', '/c', '/O2', '/GR']), ())

    def test_pinned_recipes_pass_no_root(self):
        # If a pinned recipe ever gains /I, the include wording in docs/drafter-card.md is stale.
        for path in sorted((ROOT / 'reconstruction/recipes').glob('*.json')):
            with self.subTest(recipe=path.name):
                self.assertEqual(pipeline.recipe_include_roots(json.loads(path.read_text())['flags']), ())


class AttemptCharge(unittest.TestCase):
    """Which runs count against a unit's attempt budget."""

    def setUp(self):
        self.attempt = load_script('attempt')
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.log = self.tmp / 'attempts.jsonl'

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def log_run(self, code):
        counted, free = self.attempt.charge(code, False, self.log)
        with open(self.log, 'a') as f:
            f.write(json.dumps({'exit': code, 'counted': counted, **({'free_compile_failure': True} if free else {})})
                    + '\n')
        return counted, free

    def test_compile_failures_are_free_up_to_the_cap(self):
        cap = self.attempt.FREE_COMPILE_FAILURES
        self.assertEqual(cap, 3)
        for _ in range(cap):
            self.assertEqual(self.log_run(3), (False, True))
        self.assertEqual(self.log_run(3), (True, False))
        self.assertEqual(self.attempt.counted_attempts(self.log), 1)

    def test_comparisons_always_count_and_do_not_use_the_free_failures(self):
        self.assertEqual(self.log_run(1), (True, False))
        self.assertEqual(self.log_run(0), (True, False))
        self.assertEqual(self.log_run(3), (False, True))
        self.assertEqual(self.attempt.counted_attempts(self.log), 2)

    def test_binding_only_runs_never_count(self):
        self.assertEqual(self.attempt.charge(1, True, self.log), (False, False))

    def test_host_refusals_never_count_and_use_no_free_failure(self):
        for code in (42, 43, 44, 45):
            self.assertEqual(self.log_run(code), (False, False))
        self.assertEqual(self.attempt.counted_attempts(self.log), 0)
        self.assertEqual(self.log_run(3), (False, True))
        # Comparator errors (2) and anything unknown still count.
        self.assertEqual(self.log_run(2), (True, False))
        self.assertEqual(self.log_run(7), (True, False))

    def test_old_logs_without_the_field(self):
        self.log.write_text(json.dumps({'exit': 3, 'counted': True}) + '\n')
        self.assertEqual(self.attempt.charge(3, False, self.log), (False, True))
        self.assertEqual(self.attempt.counted_attempts(self.log), 1)


class ReproduceSummaries(unittest.TestCase):
    def test_each_run_keeps_its_own_summary(self):
        sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
        import reproduce_records
        with tempfile.TemporaryDirectory() as tmp:
            first = reproduce_records.save_summary(tmp, {'records': 247}, now=0)
            second = reproduce_records.save_summary(tmp, {'records': 8}, now=0)
            self.assertNotEqual(first, second)
            self.assertEqual(json.loads(first.read_text()), {'records': 247})
            self.assertEqual(json.loads(second.read_text()), {'records': 8})
            self.assertEqual(json.loads((Path(tmp) / 'summary.json').read_text()), {'records': 8})
            self.assertEqual(len(list((Path(tmp) / 'summaries').iterdir())), 2)


if __name__ == '__main__':
    unittest.main()
