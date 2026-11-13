import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import lint_reconstruction
import static_generate
import static_template_v1 as template


class StaticGeneratorTest(unittest.TestCase):
    def test_extract_requires_exact_reference_shape(self):
        def row(text): return [0, '', text, []]
        rows = [row('lea rcx, [rip] # 0x1010'), row('lea rdx, [rip] # 0x1020'),
                row('call 0x1030 <symbol>'), row('lea rcx, [rip] # 0x1040'), row('jmp 0x1050 <symbol>')]
        self.assertEqual(static_generate.extract(rows, 0x1000),
                         {'descriptor-rva': 16, 'object-rva': 32, 'teardown-rva': 64,
                          'construct-rva': 48, 'atexit-rva': 80})
        with self.assertRaises(ValueError):
            static_generate.extract(rows[:-1], 0x1000)
        with self.assertRaises(ValueError):
            static_generate.extract(rows + [row('call 0x1060')], 0x1000)

    def test_static_template_lints_and_identifies_range(self):
        cls, header, cpp, origin, params = template.emit(0x1234, 39)
        self.assertEqual(cls, 'Static1230')
        self.assertEqual(params, {'entry-rva': 0x1234, 'size': 39})
        self.assertEqual(origin['template_digest'], template.template_digest())
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'builds').mkdir(); (root / 'builds/target.json').write_text((ROOT / 'builds/target.json').read_text())
            (root / 'findings').mkdir(); (root / template.EVIDENCE).write_text('fixture')
            recipe = root / template.RECIPE; recipe.parent.mkdir(parents=True); recipe.write_text('{}')
            area = root / 'reconstruction/static'; area.mkdir()
            (area / f'{cls}.h').write_text(header); (area / f'{cls}.cpp').write_text(cpp)
            self.assertEqual(lint_reconstruction.lint_tree(root), [])
        with self.assertRaises(ValueError): template.emit(0x1234, 38)


if __name__ == '__main__': unittest.main()
