import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import census_leaf_generate as generator
import census_leaf_template_v1 as template
import lint_reconstruction


def rows(*instructions):
    return [[0, '', instruction, []] for instruction in instructions]


class CensusLeafTests(unittest.TestCase):
    def test_extract_requires_complete_shape_and_own_target(self):
        self.assertEqual(generator.extract(rows('ret 0x0'), 0x1000, 'empty'), {})
        self.assertEqual(generator.extract(rows('jmp 0x1234'), 0x1000, 'forward'), {'target-rva': 0x234})
        self.assertEqual(generator.extract(rows('lea rax, [rip + 0x10] # 0x1456', 'ret'),
                                           0x1000, 'address'), {'target-rva': 0x456})
        for kind, instructions in [('empty', rows('ret 0x8')), ('empty', rows('nop', 'ret')),
                                   ('forward', rows('call 0x1234')), ('forward', rows('jmp 0x100')),
                                   ('forward', rows('jmp 0x1234', 'ret')),
                                   ('address', rows('lea rcx, [rip] # 0x1456', 'ret')),
                                   ('address', rows('lea rax, [rip] # 0x1456'))]:
            with self.assertRaises(ValueError):
                generator.extract(instructions, 0x1000, kind)

    def test_templates_lint_and_keep_signature_limit_explicit(self):
        self.assertEqual(len({template.origin(kind)['family'] for kind in template.KINDS}), 3)
        for kind in template.KINDS:
            method, header, source = template.emit('BSFixture', kind, True)
            prefix = template.header('BSFixture', method, kind, rva=0x1234, size=8, owner_is_rtti=True)
            self.assertIn('original signature is unknown', prefix)
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for path in ('builds/target.json', template.RECIPE):
                    destination = root / path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text((ROOT / path).read_text())
                (root / 'findings').mkdir()
                (root / template.EVIDENCE).write_text('synthetic fixture')
                area = root / 'reconstruction/bsengine'
                area.mkdir(parents=True)
                (area / 'BSFixture.h').write_text(prefix + header)
                (area / 'BSFixture.cpp').write_text(prefix + source)
                self.assertEqual(lint_reconstruction.lint_tree(root), [])

    def test_refuses_name_injection_and_overwrites(self):
        for owner, kind, virtual in [('Bad;Name', 'empty', True), ('Valid', 'wrong', True),
                                     ('Valid', 'empty', 1)]:
            with self.assertRaises(ValueError):
                template.emit(owner, kind, virtual)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.cpp'
            generator.write_new(path, 'first')
            generator.write_new(path, 'first')
            with self.assertRaises(ValueError):
                generator.write_new(path, 'second')


if __name__ == '__main__':
    unittest.main()
