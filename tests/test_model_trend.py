"""Exercise recorded attribution, history and generated graphics."""
from collections import Counter
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_model_trend as trend


class Attribution(unittest.TestCase):
    def test_families_and_unknown(self):
        for claim, family in [('claude-fable', 'Claude'), ('haiku', 'Claude'), ('sonnet', 'Claude'),
                              ('opus', 'Claude'), ('gpt-6.1-terra', 'GPT / Codex'),
                              ('Codex GPT-6.1 Sol', 'GPT / Codex'), ('luna', 'GPT / Codex'),
                              ('tools/stamp.py (Sol)', 'Scripts and tools'),
                              ('a person', 'Not reported'), ('Claude and GPT-6', 'Not reported')]:
            with self.subTest(claim=claim):
                self.assertEqual(trend.model_claim(claim)[0], family)

    def test_precedence_and_no_reviewer_guess(self):
        fn = {'id': 'b-0x1', 'drafter_model': 'gpt-6.1-terra'}
        source = b'// Drafted by claude-sonnet-5-5\n#include "a.h"'
        self.assertEqual(trend.attribution(fn, {}, {fn['id']}, source)[0:3:2], ('GPT / Codex', 'Per-function record'))
        self.assertEqual(trend.attribution({'id': fn['id']}, {}, {fn['id']}, source)[0:3:2], ('Scripts and tools', 'Family manifest'))
        self.assertEqual(trend.attribution({'id': fn['id']}, {}, set(), source)[0:3:2], ('Claude', 'Unit header'))
        self.assertEqual(trend.attribution({'id': fn['id']}, {'reviewer_model': 'opus'}, set(), None)[0], 'Not reported')
        self.assertEqual(trend.attribution({'id': fn['id'], 'drafter_model': 'unknown'}, {}, {fn['id']}, source)[0], 'Not reported')


class History(unittest.TestCase):
    def test_utc_days_adjustments_and_graphics(self):
        def fn(rva, size):
            return {'id': f'b-0x{rva:x}', 'build_id': 'b', 'rva': rva, 'size': size, 'status': 'matched'}
        data = {'one': [fn(1, 10)], 'two': [fn(1, 12), fn(2, 3)], 'three': [fn(2, 3)]}
        class Blobs:
            def read(self, rev, path):
                return json.dumps({'functions': data[rev]}).encode() if path == 'data/progress.json' else None
        log = 'one 2026-01-01T01:00:00+04:00\ntwo 2026-01-01T05:00:00+04:00\nthree 2026-01-02T01:00:00+00:00\n'
        with patch.object(trend.subprocess, 'check_output', side_effect=['false\n', log]), patch.object(trend, 'generated_members', return_value=set()):
            rows, current = trend.history('HEAD', Blobs())
        self.assertEqual(rows['2025-12-31']['families']['Not reported'], 10)
        self.assertEqual(rows['2026-01-01']['correction_bytes'], 2)
        self.assertEqual(rows['2026-01-02']['revoked_bytes'], 12)
        self.assertEqual(rows['2026-01-02']['total_bytes'], 3)
        self.assertEqual(len(current), 1)
        for render in (trend.render, trend.render_cumulative):
            self.assertEqual(render(rows), render(rows))
            ET.fromstring(render(rows))

    def test_clipping(self):
        def row(value):
            return {'families': Counter({'Claude': value}), 'models': Counter({'opus': value}),
                    'total_bytes': value, 'total_functions': 1}
        rows = {'2026-01-01': row(100), '2026-01-02': row(120), '2026-01-03': row(5000)}
        self.assertLess(trend.chart_limit([100, 120, 5000]), 5000)
        graphic = trend.render(rows)
        self.assertIn('4.9 KiB', graphic)
        self.assertIn('stroke-width="3"', graphic)
        ET.fromstring(graphic)

    def test_shallow_refused(self):
        with patch.object(trend.subprocess, 'check_output', return_value='true\n'):
            with self.assertRaisesRegex(ValueError, 'shallow'):
                trend.history('HEAD', None)


if __name__ == '__main__':
    unittest.main()
