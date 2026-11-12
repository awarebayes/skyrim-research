"""tools/sampling_packet.py: re-run comparison and verdict parsing on synthetic records."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import sampling_packet as sp  # noqa: E402
from source_digest import tu_digest  # noqa: E402


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


class BaseCommit(unittest.TestCase):
    """The label-only base commit is found with the file list the match record named at that commit."""

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=t',
                               '-c', 'user.email=t@example.invalid', *args],
                              check=True, capture_output=True, text=True).stdout.strip()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, files, msg):
        self.write(self.record_path, json.dumps({'source': {'translation_unit': files,
                                                            'digest': tu_digest(self.root, files)}}))
        self.git('add', '-A')
        self.git('commit', '-q', '-m', msg)
        return self.git('rev-parse', 'HEAD'), tu_digest(self.root, files)

    def test_header_added_to_the_closure_after_approval(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.record_path = 'reports/b/0x10.json'
        self.git('init', '-q')
        self.write('src/X.cpp', '// unit X\nint f() { return 1; }\n')
        base, approved = self.commit(['src/X.cpp'], 'approved unit')
        # The closure later gains a header the approved tree did not have; only labels change.
        self.write('src/X.h', '// label\n')
        self.write('src/X.cpp', '// unit X, relabelled\nint f() { return 1; }\n')
        files = ['src/X.cpp', 'src/X.h']
        _, current = self.commit(files, 'label-only change')
        self.write('reports/b/0x10.review.json', json.dumps(
            {'previous_source_digest': approved, 'source_digest': current, 'size': 4}))
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'review record')
        out, problems = sp.label_packet(self.root, {'label_only': {'src/X': ['0x10']}},
                                        {'0x10': 'AGREE'}, build='b')
        text = '\n'.join(out)
        self.assertIn(f'base commit with that digest: {base}', text)
        self.assertIn('translation unit at the base commit: src/X.cpp', text)
        self.assertEqual(problems, [])


if __name__ == '__main__':
    unittest.main()
