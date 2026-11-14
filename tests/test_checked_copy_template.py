"""Synthetic complete-reference and template checks; no game material."""
from pathlib import Path
import struct
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import census_checked_copy_generate as generator
import checked_copy_template_v1 as template


class CheckedCopyTests(unittest.TestCase):
    def fixture(self):
        code = b'\xe8' + struct.pack('<i', 8192-4101) + b'\xc3'
        image = NS(image_base=0, section_for=lambda r: NS(),
                   read=lambda *args: (NS(flags=0x20000000), code))
        section = NS(data=b'\xe8'+bytes(4)+b'\xc3', relocs=[NS(offset=1, kind=4, symbol=1)])
        candidate = NS(symbols={0: NS(name='Example', is_function=True, storage=2, value=0, section=1),
                                    1: NS(name='helper')}, section=lambda n: section)
        return image, candidate, section

    def test_bindings_recalculate_each_member(self):
        image, obj, _ = self.fixture()
        self.assertEqual(generator.bindings(image, 4096, 6, obj, 'Example'), {'helper':8192})

    def test_every_nonreference_byte_checked(self):
        image, obj, section = self.fixture()
        section.data = section.data[:-1]+b'\x90'
        with self.assertRaisesRegex(ValueError, 'non-reference'):
            generator.bindings(image, 4096, 6, obj, 'Example')

    def test_missing_or_wrong_reference_is_refused(self):
        for mutation in ('missing', 'kind', 'offset'):
            image, obj, section = self.fixture()
            if mutation == 'missing': section.relocs=[]
            elif mutation == 'kind': section.relocs[0].kind=5
            else: section.relocs[0].offset=2
            with self.assertRaises(ValueError):
                generator.bindings(image, 4096, 6, obj, 'Example')

    def test_changed_extraction_dependency_refused(self):
        image, obj, _ = self.fixture()
        name = next(iter(generator.EXTRACTION_DEPENDENCIES))
        with patch.dict(generator.EXTRACTION_DEPENDENCIES, {name: "0"*64}):
            with self.assertRaisesRegex(ValueError, "extraction dependency differs"):
                generator.bindings(image, 4096, 6, obj, "Example")

    def test_extent_and_identity_refused(self):
        image, obj, section = self.fixture()
        with self.assertRaisesRegex(ValueError, 'identity'):
            generator.bindings(image, 4096, 6, obj, 'Missing')
        section.data+=b'\xc3'
        with self.assertRaisesRegex(ValueError, 'extent'):
            generator.bindings(image, 4096, 6, obj, 'Example')

    def test_nonzero_reference_addend_refused(self):
        image, obj, section = self.fixture()
        section.data = b'\xe8'+struct.pack('<i', 1)+b'\xc3'
        with self.assertRaisesRegex(ValueError, 'nonzero addend'):
            generator.bindings(image, 4096, 6, obj, 'Example')

    def test_missing_confirmation_does_not_link_any_report(self):
        import accept_function as af
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            out = root / '.local' / 'candidates'
            task = out / 'task'
            task.mkdir(parents=True)
            selected = [dict(rva=4096+i) for i in range(20)]
            (out / 'selection.json').write_text(json.dumps(dict(members=selected)))
            (out / 'all.txt').write_text(str(task)+'\n')
            (task / 'task.json').write_text(json.dumps(dict(functions=[dict(rva=4096)])))
            original = dict(functions=[dict(rva=4096)])
            with patch.object(generator, 'ROOT', root), patch.object(af, 'load', return_value=(original, {})), patch.object(af, 'validate_match', side_effect=ValueError('second host absent')):
                with self.assertRaisesRegex(ValueError, 'second host absent'):
                    generator.records_to_spec(out)
            self.assertNotIn('report', original['functions'][0])
            self.assertFalse((out / 'family-spec.json').exists())

    def test_source_is_normal_library_wrapper(self):
        owner, symbol, h, cpp = template.emit(4096, 171)
        self.assertIn('return memcpy_s(destination, destinationSize, source, count);', cpp)
        self.assertIn('class '+owner, h)
        self.assertIn('static int Copy(', h)
        self.assertIn('GUESS(low)', h)
        import lint_review_readiness
        self.assertEqual(lint_review_readiness.origin_statement_problems(owner+'.h', h), [])
        self.assertEqual(lint_review_readiness.origin_statement_problems(owner+'.cpp', cpp), [])
        import tempfile
        import lint_reconstruction
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            area = root/'reconstruction/buffers'
            area.mkdir(parents=True)
            for name in [template.EVIDENCE, template.RECIPE]:
                path = root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('synthetic metadata fixture')
            for suffix, text in [('.h', h), ('.cpp', cpp)]:
                name = f'reconstruction/buffers/{owner}{suffix}'
                (root/name).write_text(text)
                self.assertEqual(lint_reconstruction.lint_file(root, name, template.BUILD), [])
        self.assertNotIn('struct ', h+cpp)
        self.assertEqual(template.origin()['template_digest'], generator.hashlib.sha256(Path(template.__file__).read_bytes()).hexdigest())
        for rva, size in [(True, 171), (4096, 170), (0, 171)]:
            with self.assertRaises(ValueError): template.emit(rva, size)


if __name__ == '__main__':
    unittest.main()
