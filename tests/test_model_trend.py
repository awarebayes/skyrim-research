"""Model attribution is informational and must not invent evidence or lose adjustments."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_model_trend as trend


class Labels(unittest.TestCase):
    def test_only_explicit_header_claims_are_classified(self):
        examples = {
            b'// Drafted by claude-haiku-5-5.\n#include "x.h"': 'Claude',
            b'// Drafted by gpt-6-luna.\n#include "x.h"': 'GPT / Codex',
            b'// Drafted by Claude and GPT-6.\n#include "x.h"': 'Mixed',
            b'// Drafted by GPT-6 (recipe) and Terra (generator).\n#include "x.h"': 'Generated / tools',
            b'// Drafted by a person assisted by GPT-6.\n#include "x.h"': 'Mixed',
            b'// Reviewer: Claude\n#include "x.h"\n// Drafted by Claude': 'Unknown',
            b'// Drafted by a person.\n#include "x.h"': 'Unknown',
        }
        for source, expected in examples.items():
            with self.subTest(source=source):
                self.assertEqual(trend.classify(source), expected)

    def test_missing_and_shallow_history_fail_safely(self):
        self.assertEqual(trend.classify(None), 'Unknown')
        with patch.object(trend.subprocess, 'check_output', return_value='true\n'):
            with self.assertRaisesRegex(ValueError, 'shallow'):
                trend.history('HEAD', None)


class History(unittest.TestCase):
    def test_accept_revoke_reaccept_and_size_correction(self):
        def progress(functions):
            return json.dumps({'functions': functions}).encode()
        def fn(rva, size, report):
            return {'build_id': 'build', 'rva': rva, 'size': size,
                    'status': 'matched', 'report': report}
        report = json.dumps({'source': {'compiled': 'unit.cpp'}}).encode()
        class Blobs:
            def read(self, commit, path):
                return {
                    ('one', 'data/progress.json'): progress([fn(1, 10, 'r.json')]),
                    ('two', 'data/progress.json'): progress([fn(1, 12, 'r.json'), fn(2, 3, 'missing')]),
                    ('three', 'data/progress.json'): progress([fn(2, 3, 'missing')]),
                    ('four', 'data/progress.json'): progress([fn(1, 10, 'r.json'), fn(2, 3, 'missing')]),
                    ('one', 'r.json'): report, ('four', 'r.json'): report,
                    ('one', 'unit.cpp'): b'// Drafted by Claude\n#include "x.h"',
                    ('four', 'unit.cpp'): b'// Drafted by GPT-6\n#include "x.h"',
                }.get((commit, path))
        log = ('one 2026-11-11T03:30:00+04:00\n'
               'two 2026-11-11T05:00:00+04:00\n'
               'three 2026-11-12T12:00:00+00:00\n'
               'four 2026-11-13T12:00:00+00:00\n')
        with patch.object(trend.subprocess, 'check_output', side_effect=['false\n', log]):
            rows, current = trend.history('HEAD', Blobs())
        self.assertEqual(rows['2026-11-10']['Claude'], 10)  # converted to UTC
        self.assertEqual(rows['2026-11-11']['Unknown'], 3)
        self.assertEqual(rows['2026-11-11']['correction_bytes'], 2)
        self.assertEqual(rows['2026-11-12']['revoked_bytes'], 12)
        self.assertEqual(rows['2026-11-13']['GPT / Codex'], 10)
        self.assertEqual(sum(v[0] for v in current.values()), 13)
        graphic = trend.render(rows, 'a' * 40)
        self.assertIn('revoked 12 bytes', graphic)
        self.assertIn('size corrections +2 bytes', graphic)
        self.assertIn('Unknown', graphic)


if __name__ == '__main__':
    unittest.main()
