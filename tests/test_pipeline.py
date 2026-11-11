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

    def test_missing_inputs_give_a_reason(self):
        path, why = disasm.write_side_by_side('/nonexistent/x', None, None, 'x.obj', 'f', 0, 1)
        self.assertIsNone(path)
        self.assertIn('llvm-objdump', why)


if __name__ == '__main__':
    unittest.main()
