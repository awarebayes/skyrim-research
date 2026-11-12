"""tools/sampling_packet.py: re-run comparison and verdict parsing on synthetic records."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import sampling_packet as sp  # noqa: E402


def record(digest='d1', section='s1', hosts=('a', 'b'), result=('pass', 'all-checks-passed')):
    return {'source': {'digest': digest},
            'runs': [{'compiled_on': h, 'report': {'result': result[0], 'reason': result[1],
                                                   'candidate': {'code_section_sha256': section}}}
                     for h in hosts for _ in range(2)]}


class Verdicts(unittest.TestCase):
    def test_rows_keep_their_verdict_with_line_endings(self):
        rows = ['label_only bsengine/X 0x10 runs 4/4 hash_same True AGREE\n',
                'label_only bsengine/X 0x20 runs 4/4 hash_same False DISAGREE\r\n',
                'reviewed   forms/Y    0x30 runs 4/4 AGREE',
                'agree 2 of 3\n']
        self.assertEqual(sp.parse_rows(rows), {'0x10': 'AGREE', '0x20': 'DISAGREE', '0x30': 'AGREE'})

    def test_compare(self):
        self.assertTrue(sp.compare(record(), record())[0])
        self.assertTrue(sp.compare(record(), record())[1].endswith('AGREE'))
        for other in (record(digest='d2'), record(section='s2'), record(hosts=('a',)),
                      record(result=('fail', 'code-mismatch'))):
            ok, row = sp.compare(record(), other)
            self.assertFalse(ok)
            self.assertTrue(row.endswith('DISAGREE'))

    def test_comment_only(self):
        diff = '--- a/x\n+++ b/x\n@@ -1 +1 @@\n-// old\n+// new\n+\n'
        self.assertEqual(sp.comment_only(diff), [])
        self.assertEqual(sp.comment_only(diff + '+int x;\n'), ['+int x;'])


if __name__ == '__main__':
    unittest.main()
