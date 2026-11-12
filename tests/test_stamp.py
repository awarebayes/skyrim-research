import importlib.util
from pathlib import Path
import unittest
import json
import tempfile

spec = importlib.util.spec_from_file_location('stamp_lane', Path(__file__).resolve().parents[1] / 'tools/stamp.py')
stamp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stamp)


class StampSafetyTests(unittest.TestCase):
    def test_resume_requires_current_translation_unit_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unit = root / 'reconstruction' / 'example'
            unit.mkdir(parents=True)
            (unit / 'unit.cpp').write_text('#include "unit.h"\n')
            header = unit / 'unit.h'
            header.write_text('#pragma once\n')
            task = root / 'task'
            task.mkdir()
            (task / 'task.json').write_text(json.dumps({'compiled': 'reconstruction/example/unit.cpp'}))
            record = {'task': str(task), 'source_digest': stamp.task_digest(root, task)}
            stamp.check_resume([record], root)
            with self.assertRaisesRegex(ValueError, 'missing source digest'):
                stamp.check_resume([{'task': str(task)}], root)
            header.write_text('#pragma once\n// changed\n')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                stamp.check_resume([record], root)

    def test_zero_padding_after_vptr(self):
        header, _ = stamp.emit_leaf('Example', 'Read', family='member', width=8,
                                    value=8, virtual=True, name_label='COMMUNITY(example@revision, licence)')
        self.assertNotIn('padding[', header)
        self.assertIn('void* member;', header)

    def test_wrong_target_is_refused(self):
        with self.assertRaisesRegex(stamp.UnsafeCandidate, 'wrong-target'):
            stamp.validate_bindings({'call': 0x1000}, {'call': 0x2000})

    def test_missing_and_extra_reference_is_refused(self):
        with self.assertRaisesRegex(stamp.UnsafeCandidate, 'reference-fields'):
            stamp.validate_bindings({'call': 0x1000}, {})
        with self.assertRaisesRegex(stamp.UnsafeCandidate, 'reference-fields'):
            stamp.validate_bindings({}, {'call': 0x1000})

    def test_name_clash_and_existing_class_are_refused(self):
        args = dict(owner='Example', method='Read', existing_classes=set(),
                    names={'Example::Read': {1, 2}}, name_rva=1, rva=1)
        with self.assertRaisesRegex(stamp.UnsafeCandidate, 'name-clash'):
            stamp.validate_identity(**args)
        args['names'] = {'Example::Read': {1}}
        args['existing_classes'] = {'Example'}
        with self.assertRaisesRegex(stamp.UnsafeCandidate, 'existing-unit'):
            stamp.validate_identity(**args)

    def test_template_and_unaligned_offset_are_refused(self):
        with self.assertRaisesRegex(stamp.UnsafeCandidate, 'template-owned'):
            stamp.validate_identity('Example<int>', 'Read', existing_classes=set(), names={}, name_rva=1, rva=1)
        with self.assertRaisesRegex(stamp.UnsafeCandidate, 'invalid-offset'):
            stamp.emit_leaf('Example', 'Read', family='member', width=4, value=9,
                            virtual=True, name_label='GUESS(low)')

    def test_missing_name_label_is_refused(self):
        with self.assertRaisesRegex(stamp.UnsafeCandidate, 'name-origin'):
            stamp.emit_leaf('Example', 'Read', family='constant', width=4, value=1,
                            virtual=False, name_label='')

    def test_labels_and_address(self):
        header, source = stamp.emit_leaf('Example', 'Slot2', family='member-address', width=4,
                                         value=12, virtual=True, name_label='GUESS(low)')
        self.assertIn('// Slot2: GUESS(low)', header)
        self.assertIn('GUESS(low)', header)
        self.assertIn('return &member;', source)


if __name__ == '__main__':
    unittest.main()


class GeneratorDecodeTests(unittest.TestCase):
    def test_leaf_decoder_and_reject(self):
        self.assertEqual(stamp.decode_leaf(bytes.fromhex('b878563412c3')), ('constant', 4, 0x12345678))
        self.assertEqual(stamp.decode_leaf(bytes.fromhex('488b4108c3')), ('member', 8, 8))
        self.assertEqual(stamp.decode_leaf(bytes.fromhex('8b8178563412c3')), ('member', 4, 0x12345678))
        self.assertIsNone(stamp.decode_leaf(bytes.fromhex('b87856341290')))
        self.assertIsNone(stamp.decode_leaf(b''))

    def test_negative_displacement_rejected(self):
        kind, width, offset = stamp.decode_leaf(bytes.fromhex('8b41fcc3'))
        with self.assertRaises(stamp.UnsafeCandidate):
            stamp.emit_leaf('Example', 'Read', family=kind, width=width, value=offset,
                            virtual=True, name_label='GUESS(low)')

    def test_runner_refuses_remote_and_boat(self):
        config = {'attempt': 'selected', 'hosts': {'selected': {'backend': 'local', 'loader': 'wine', 'host_id': 'mac-wine'}}}
        self.assertEqual(stamp.require_local_wine(config)['backend'], 'local')
        for backend in ('ssh', 'boat'):
            config['hosts']['selected']['backend'] = backend
            with self.assertRaises(ValueError):
                stamp.require_local_wine(config)

class InstallTests(unittest.TestCase):
    def test_install_and_refuse_clash_or_stale_digest(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staging, dest = root / 'stage', root / 'checkout'
            unit = staging / 'reconstruction' / 'forms'
            unit.mkdir(parents=True)
            (dest / 'reconstruction').mkdir(parents=True)
            (unit / 'Example.h').write_text('#pragma once\n')
            (unit / 'Example.cpp').write_text('#include "Example.h"\n')
            task = staging / 'tasks' / 'example'
            task.mkdir(parents=True)
            (task / 'task.json').write_text(json.dumps({'compiled': 'reconstruction/forms/Example.cpp'}))
            digest = stamp.task_digest(staging, task)
            row = {'task': str(task), 'rva': 1, 'family': 'const-return', 'source_digest': digest}
            (staging / 'const-return.jsonl').write_text(json.dumps(row) + '\n')
            (staging / 'results.jsonl').write_text(json.dumps(dict(row, result='pass', exit=0)) + '\n')
            args = SimpleNamespace(source=str(staging), dest=str(dest), family='const-return')
            stamp.install(args)
            self.assertEqual((dest / 'reconstruction/forms/Example.h').read_text(), '#pragma once\n')
            with self.assertRaisesRegex(ValueError, 'clashes'):
                stamp.install(args)
            (unit / 'Example.h').write_text('// changed\n')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                stamp.install(args)


class GeneratorLayoutTests(unittest.TestCase):
    """Original synthetic inputs exercise the real generation/install path, without a runner."""

    def setUp(self):
        import struct
        import hashlib
        from types import SimpleNamespace
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.main = self.root / 'repo'
        self.wt = self.main / '.local/wt'
        self.out = self.main / '.local/out'
        for directory in ['.local', 'reconstruction/bsengine', 'reconstruction/recipes',
                          'tools/verifier', 'builds', 'findings']:
            (self.wt / directory).mkdir(parents=True, exist_ok=True)
        (self.main / 'reconstruction').mkdir()
        (self.wt / 'tools/verifier/attempt').write_text('synthetic runner placeholder')
        (self.wt / stamp.RECIPE).write_text('{}')
        (self.wt / 'tools/verifier/pinned.sha256').write_text('synthetic toolchain pin')
        (self.wt / stamp.EVIDENCE).write_text('Synthetic fixture evidence')
        image = bytearray(0x280)
        struct.pack_into('<I', image, 0x3c, 0x80)
        struct.pack_into('<H', image, 0x86, 1)
        struct.pack_into('<IIII', image, 0xa0, 0x80, 0x1000, 0x80, 0x200)
        for offset in [0x200, 0x220, 0x240, 0x260]:
            image[offset:offset + 6] = bytes.fromhex('b801000000c3')
        (self.root / 'image').write_bytes(image)
        target = dict(build_id=stamp.BUILD, image_sha256=hashlib.sha256(image).hexdigest())
        (self.wt / 'builds/target.json').write_text(json.dumps(target))
        owners = ['BSAlpha', 'ExtraBeta', 'Wandering', 'bhkSynthetic']
        functions = [dict(rva=0x1000 + i * 0x20, names=[], owner=dict(
            **{'class': cls}, slot=2)) for i, cls in enumerate(owners)]
        (self.root / 'functions.jsonl').write_text(''.join(json.dumps(f) + '\n' for f in functions))
        (self.root / 'classes.jsonl').write_text(json.dumps({'class': 'ExtraBeta', 'parent': 'BSBase'}) + '\n')
        (self.root / 'progress.json').write_text(json.dumps({'functions': []}))
        (self.root / 'families.json').write_text(json.dumps([dict(rank=11, shape='synthetic')]))
        (self.root / 'census.tsv').write_text('rva\tsize\tshape\ttier\n' + ''.join(
            f'{f["rva"]:x}\t6\tsynthetic\t1\n' for f in functions))
        self.cfg = dict(main=str(self.main), worktree=str(self.wt),
                        **{key: str(self.root / filename) for key, filename in [
                            ('functions', 'functions.jsonl'), ('classes', 'classes.jsonl'),
                            ('progress', 'progress.json'), ('families', 'families.json'),
                            ('census', 'census.tsv'), ('image', 'image')]})
        (self.root / 'config.json').write_text(json.dumps(self.cfg))
        self.args = SimpleNamespace(config=str(self.root / 'config.json'), out=str(self.out),
                                    family='const-return', resume=False, limit=None)

    def generate(self):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            stamp.generate(self.args)
        return [json.loads(l) for l in (self.out / 'const-return.jsonl').read_text().splitlines()]

    def test_generate_final_layout_labels_area_and_lint(self):
        from lint_reconstruction import lint_tree
        rows = self.generate()
        self.assertEqual(len(rows), 2)
        self.assertEqual([r['area']['how'] for r in rows], ['prefix', 'base-prefix'])
        names = []
        for row in rows:
            self.assertTrue(row['compiled'].startswith('reconstruction/bsengine/'))
            self.assertEqual(row['source_digest'], stamp.task_digest(self.out, row['task']))
            self.assertEqual(row['source_digest'], stamp.task_digest(self.wt, row['task']))
            text = (self.out / row['compiled']).read_text()
            self.assertIn('"generator_version":"2"', text)
            self.assertIn(stamp.template_digest('const-return'), text)
            self.assertIn('// Slot2: GUESS(low)', text)
            names += [row['compiled'], str(Path(row['compiled']).with_suffix('.h'))]
        self.assertEqual(lint_tree(self.wt, names), [])
        summary = json.loads((self.out / 'const-return.summary.json').read_text())
        self.assertEqual(summary['skipped'], {'no-area-rule': 1, 'unsupported-class-layout': 1})

    def test_generate_refuses_wrong_image(self):
        (self.root / 'image').write_bytes(b'wrong synthetic image')
        with self.assertRaisesRegex(ValueError, 'pinned target'):
            self.generate()

    def test_generate_refuses_overwrite_and_staging_resume_edit(self):
        rows = self.generate()
        with self.assertRaisesRegex(ValueError, 'index exists'):
            self.generate()
        self.args.resume = True
        (self.out / rows[0]['compiled']).write_text('// edited fixture')
        with self.assertRaisesRegex(ValueError, 'staged source changed'):
            self.generate()

    def test_resume_refuses_changed_task_and_recipe(self):
        rows = self.generate()
        stamp.check_resume(rows, self.wt)
        recipe = self.wt / stamp.RECIPE
        recipe.write_text('{"flags": ["/O1"]}')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            stamp.check_resume(rows, self.wt)
        recipe.write_text('{}')
        task = Path(rows[0]['task']) / 'task.json'
        raw = json.loads(task.read_text())
        raw['functions'][0]['size'] += 1
        task.write_text(json.dumps(raw))
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            stamp.check_resume(rows, self.wt)

    def test_real_layout_install_refuses_identity_and_duplicate_result(self):
        import contextlib
        import io
        from types import SimpleNamespace
        rows = self.generate()
        dest = self.root / 'scratch'
        (dest / 'reconstruction').mkdir(parents=True)
        results = [dict(r, result='pass', exit=0) for r in rows]
        log = self.out / 'results.jsonl'
        log.write_text(''.join(json.dumps(r) + '\n' for r in results))
        args = SimpleNamespace(source=self.out, dest=dest, family='const-return')
        with contextlib.redirect_stdout(io.StringIO()):
            stamp.install(args)
        self.assertEqual(len(list((dest / 'reconstruction').rglob('*.cpp'))), 2)
        log.write_text(''.join(json.dumps(r) + '\n' for r in results + [results[0]]))
        with self.assertRaisesRegex(ValueError, 'duplicate result'):
            stamp.install(args)
        log.write_text(''.join(json.dumps(r) + '\n' for r in results))
        task = Path(rows[0]['task']) / 'task.json'
        raw = json.loads(task.read_text())
        raw['functions'][0]['rva'] = '0x1999'
        task.write_text(json.dumps(raw))
        with self.assertRaisesRegex(ValueError, 'task identity mismatch'):
            stamp.install(args)

    def test_area_cycles_and_unknowns_have_no_fallback(self):
        self.assertEqual(stamp.resolve_area('Unknown', {}, {}), (None, 'no-area-rule', None))
        classes = {'One': {'parent': 'Two'}, 'Two': {'parent': 'One'}}
        self.assertEqual(stamp.resolve_area('One', classes, {})[0], None)
        classes['Two']['parent'] = 'Actor'
        self.assertEqual(stamp.resolve_area('One', classes, {}), ('actors', 'base-prefix', 'Actor'))
        self.assertEqual(stamp.resolve_area('One', classes, {'Two': 'inventory'}),
                         ('inventory', 'base-unit', 'Two'))

    def test_attempt_resume_and_runner_binding(self):
        import contextlib
        import io
        from types import SimpleNamespace
        from unittest.mock import patch
        self.generate()
        runners = self.root / 'runners.json'
        config = dict(runners_schema=1, attempt='mac', hosts={'mac': dict(
            backend='local', loader='wine', host_id='mac-wine')}, confirm=[])
        runners.write_text(json.dumps(config))
        self.cfg['runners'] = str(runners)
        (self.root / 'config.json').write_text(json.dumps(self.cfg))
        args = SimpleNamespace(config=self.args.config, out=self.out, jobs=8, resume=False)
        result = SimpleNamespace(returncode=0, stdout='PASS all-checks-passed\n')
        with patch('subprocess.run', return_value=result) as run, contextlib.redirect_stdout(io.StringIO()):
            stamp.attempt_all(args)
            self.assertEqual(run.call_count, 2)
            args.resume = True
            run.reset_mock()
            stamp.attempt_all(args)
            run.assert_not_called()
        log = self.out / 'results.jsonl'
        records = [json.loads(l) for l in log.read_text().splitlines()]
        self.assertEqual(len(records), 2)
        self.assertTrue(all(r['source_digest'] and r['input_digest'] and r['runner_digest'] for r in records))
        config['hosts']['mac']['max_parallel'] = 8
        runners.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, 'runner configuration changed'):
            stamp.attempt_all(args)
        del records[0]['input_digest']
        log.write_text(''.join(json.dumps(r) + '\n' for r in records))
        with self.assertRaisesRegex(ValueError, 'missing input digest'):
            stamp.attempt_all(args)

    def test_install_preflights_all_clashes_and_ignores_failed_units(self):
        import contextlib
        import io
        from types import SimpleNamespace
        rows = self.generate()
        dest = self.root / 'scratch'
        (dest / 'reconstruction/bsengine').mkdir(parents=True)
        clash = dest / rows[-1]['compiled']
        clash.write_text('existing independent edit')
        results = [dict(r, result='pass', exit=0) for r in rows]
        log = self.out / 'results.jsonl'
        log.write_text(''.join(json.dumps(r) + '\n' for r in results))
        args = SimpleNamespace(source=self.out, dest=dest, family='const-return')
        with self.assertRaisesRegex(ValueError, 'clashes'):
            stamp.install(args)
        self.assertFalse((dest / rows[0]['compiled']).exists())
        self.assertEqual(clash.read_text(), 'existing independent edit')
        clash.unlink()
        results[-1]['result'] = 'fail'
        results[-1]['exit'] = 1
        log.write_text(''.join(json.dumps(r) + '\n' for r in results))
        with contextlib.redirect_stdout(io.StringIO()):
            stamp.install(args)
        self.assertTrue((dest / rows[0]['compiled']).exists())
        self.assertFalse((dest / rows[-1]['compiled']).exists())

    def test_install_refuses_modified_staged_inputs(self):
        from types import SimpleNamespace
        rows = self.generate()
        dest = self.root / 'scratch'
        (dest / 'reconstruction').mkdir(parents=True)
        log = self.out / 'results.jsonl'
        log.write_text(''.join(json.dumps(dict(r, result='pass', exit=0)) + '\n' for r in rows))
        args = SimpleNamespace(source=self.out, dest=dest, family='const-return')
        symbols = Path(rows[0]['task']) / 'symbols.json'
        original = symbols.read_text()
        symbols.write_text(original + ' ')
        with self.assertRaisesRegex(ValueError, 'staged input digest mismatch'):
            stamp.install(args)
        symbols.write_text(original)
        (self.out / stamp.RECIPE).write_text('{"flags": ["/O1"]}')
        with self.assertRaisesRegex(ValueError, 'staged input digest mismatch'):
            stamp.install(args)
        self.assertEqual(list((dest / 'reconstruction').rglob('*.cpp')), [])
