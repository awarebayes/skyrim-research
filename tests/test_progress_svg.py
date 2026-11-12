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
        self.map = gen.render_map(ROOT)
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
            for name in ('progress.svg', 'progress-map.svg'):
                (root / 'docs' / name).write_text('<svg/>')
            current = mock.patch.object(gen, 'render', return_value='<svg/>')
            current_map = mock.patch.object(gen, 'render_map', return_value='<svg/>')
            with current, current_map:
                check.check_progress_svg(root)
            with mock.patch.object(gen, 'render', return_value='<svg>new</svg>'), current_map:
                with self.assertRaisesRegex(ValueError, 'progress.svg is out of date'):
                    check.check_progress_svg(root)
            with current, mock.patch.object(gen, 'render_map', return_value='<svg>new</svg>'):
                with self.assertRaisesRegex(ValueError, 'progress-map.svg is out of date'):
                    check.check_progress_svg(root)
            (root / 'docs/progress.svg').unlink()
            with current, current_map:
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

    def test_every_scope_category_is_drawn_and_named(self):
        groups = gen.scope_groups(self.scope)
        self.assertEqual(sum(g['functions'] for g in groups), sum(c['functions'] for c in self.scope['categories']))
        self.assertEqual(sum(g['bytes'] for g in groups), sum(c['bytes'] for c in self.scope['categories']))
        text = ' '.join(re.findall(r'<text[^>]*>([^<]*)</text>', self.svg))
        for c in self.scope['categories']:
            self.assertIn(escape(c['label']), text)

    def test_estimates_are_labelled(self):
        for g in gen.scope_groups(self.scope):
            suffix = ' est.' if g['estimated'] else ' ·'
            self.assertIn(f'{g["functions"]:,} functions{suffix}', self.svg)

    def test_no_text_is_clipped_or_small(self):
        for svg in (self.svg, self.map):
            self.assertNotIn('clip-path', svg)
            sizes = [float(v) for v in re.findall(r'font-size:([\d.]+)px', svg)]
            self.assertGreaterEqual(min(sizes), 12)

    def test_map_is_current_and_self_contained(self):
        self.assertEqual(self.map, (ROOT / 'docs/progress-map.svg').read_text(), 'run tools/build_progress_svg.py')
        self.assertLess(len(self.map.encode()), 600_000)
        for forbidden in ('<script', '<image', '@import', 'href=', '%'):
            self.assertNotIn(forbidden, self.map)
        self.assertEqual(self.map.count('http://'), 1)

    def test_map_names_every_listed_class_once_per_tile(self):
        st = gen.stats(self.progress, ROOT)
        areas = gen.map_areas(self.scope, st)
        labels = re.findall(r'<text[^>]*class="bl">([^<]*)</text>', self.map)
        classes = [c for a in areas for c in a['classes']]
        others = [a for a in areas if a['other'] and a['other']['functions'] > 0]
        self.assertEqual(len(labels), len(classes) + len(others))
        for c in classes:
            self.assertLessEqual(c['done'], c['functions'])
            expect = f'{c["name"]}  {c["done"]}/{c["functions"]:,}' if c['done'] else c['name']
            self.assertIn(escape(expect), labels)
        shown = sum(c['done'] for c in classes)
        self.assertIn(f'{shown} of the {st["matched"]} accepted functions', self.map)
        self.assertLessEqual(shown, st['matched'])


if __name__ == '__main__':
    unittest.main()
