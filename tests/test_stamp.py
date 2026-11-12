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

    def test_labels_and_address(self):
        header, source = stamp.emit_leaf('Example', 'Slot2', family='member-address', width=4,
                                         value=12, virtual=True, name_label='GUESS(low)')
        self.assertIn('GENERATED(member-address@1)', header)
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
