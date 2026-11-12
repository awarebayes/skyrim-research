"""The progress picture is deterministic, matches the tracked data and never shows an unnamed percentage."""
from html import escape
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_progress_svg as gen

ROOT = gen.ROOT


class ProgressSvgTests(unittest.TestCase):
    def setUp(self):
        self.svg = gen.render(ROOT)
        self.progress = json.loads((ROOT / 'data/progress.json').read_text())
        self.scope = json.loads((ROOT / 'data/scope.json').read_text())

    def test_deterministic_and_current(self):
        self.assertEqual(self.svg, gen.render(ROOT))
        self.assertEqual(self.svg, (ROOT / 'docs/progress.svg').read_text(), 'run tools/build_progress_svg.py')

    def test_check_requires_the_rendered_picture(self):
        import tempfile
        from unittest import mock
        import check
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs').mkdir()
            (root / 'docs/progress.svg').write_text('<svg/>')
            with mock.patch.object(gen, 'render', return_value='<svg/>'):
                check.check_progress_svg(root)
            with mock.patch.object(gen, 'render', return_value='<svg>new</svg>'):
                with self.assertRaisesRegex(ValueError, 'progress.svg is out of date'):
                    check.check_progress_svg(root)
            (root / 'docs/progress.svg').unlink()
            with mock.patch.object(gen, 'render', return_value='<svg/>'):
                with self.assertRaisesRegex(ValueError, 'progress.svg is out of date'):
                    check.check_progress_svg(root)

    def test_self_contained_and_small(self):
        self.assertLess(len(self.svg.encode()), 600_000)
        for forbidden in ('<script', '<image', 'http://', '@import', 'href='):
            if forbidden == 'http://':
                self.assertEqual(self.svg.count('http://'), 1)  # the SVG namespace only
            else:
                self.assertNotIn(forbidden, self.svg)
        self.assertNotRegex(self.svg, r'\d{4}-\d{2}-\d{2}')

    def test_counts_match_data(self):
        matched = [f for f in self.progress['functions'] if f['status'] == 'matched']
        self.assertIn(f'{len(matched)} accepted byte-matches', self.svg)
        self.assertIn(f'({len(self.progress["functions"])} tracked)', self.svg)
        self.assertIn(f'{sum(f["size"] for f in matched):,} of ', self.svg)

    def test_scope_categories_sum_to_denominator(self):
        den = self.scope['denominators']['functions_excluding_funclets_and_thunks']
        cats = [c for c in self.scope['categories'] if c['id'] not in ('funclets', 'thunks')]
        self.assertEqual(sum(c['functions'] for c in cats), den['functions'])
        self.assertEqual(sum(c['bytes'] for c in cats), den['bytes'])
        for c in self.scope['categories']:
            self.assertIn(c['basis'], ('measured', 'estimated'))
            self.assertTrue(c['method'])

    def test_percentages_name_a_measured_denominator(self):
        texts = re.findall(r'<text[^>]*>([^<]*)</text>', self.svg)
        with_pct = [t for t in texts if '%' in t]
        self.assertTrue(with_pct)
        for t in with_pct:
            self.assertIn('(measured', t)
        self.assertIsNone(self.progress['scope']['functions'])

    def test_area_panel_labels_classes(self):
        areas = self.scope.get('areas')
        if not areas:
            self.skipTest('scope has no area breakdown')
        self.assertIn('Ordinary code by area and class', self.svg)
        drawn = [c['name'] for b in areas['blocks'] for c in b['classes']]
        self.assertGreaterEqual(sum(1 for n in drawn if f'>{escape(n)}</text>' in self.svg), 20)
        total = sum(b['functions'] for b in areas['blocks'])
        self.assertEqual(total, areas['population']['functions'])

    def test_estimates_are_labelled(self):
        for c in self.scope['categories']:
            if c['basis'] == 'estimated' and c['label'] in self.svg:
                self.assertIn(f'{c["functions"]:,} fns est.', self.svg)


if __name__ == '__main__':
    unittest.main()
