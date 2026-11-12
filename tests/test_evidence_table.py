"""The generated unit table of a batch findings file and the evidence line of a brief
(tools/ghidra/export_pack.py), on invented task directories and inventory rows only."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools' / 'ghidra'))
import export_pack as ep  # noqa: E402

BUILD = 'demo-build'
FINDING = 'findings/demo-selection.md'
TEXT = ('# Finding: demo\n\n## Interpretation and alternatives\n\nText.\n\n'
        '## Reproduction and sanitized evidence\n\nCommand.\n\n## Reviewer and outcome\n\nNot reviewed.\n')


def fn(rva, role=None):
    f = {'rva': hex(rva), 'size': 8, 'symbol': f'?F{rva:x}@Demo@@QEAAXXZ', 'function_id': f'{BUILD}-{hex(rva)}',
         'community_name': f'Demo::F{rva:x}', 'pack': f'.local/packs/{BUILD}/{hex(rva)}'}
    if role:
        f['role'] = role
    return f


def row(rva, evidence=FINDING, name=None):
    return {'id': f'{BUILD}-{hex(rva)}', 'rva': rva, 'name': name or f'Demo::F{rva:x}', 'evidence': evidence}


class UnitTable(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        (self.root / 'findings').mkdir()
        (self.root / 'data').mkdir()
        (self.root / FINDING).write_text(TEXT)
        self.rows = [row(0x100), row(0x200), row(0x300, evidence='findings/other.md'), row(0x400)]
        self.write_rows()
        group = self.root / '.local/tasks/demo-s01'
        self.task('demo-s01-demoa', 'reconstruction/forms/DemoA.cpp', [fn(0x100), fn(0x300)], group)
        self.task('demo-demob', 'reconstruction/netimmerse/DemoB.cpp', [fn(0x200), fn(0x400, role='regression')])

    def tearDown(self):
        shutil.rmtree(self.root)

    def write_rows(self):
        (self.root / 'data/progress.json').write_text(json.dumps({'functions': self.rows}))

    def task(self, task_id, compiled, functions, parent=None):
        d = (parent or self.root / '.local/tasks') / task_id
        d.mkdir(parents=True)
        (d / 'task.json').write_text(json.dumps({'task_id': task_id, 'build_id': BUILD, 'compiled': compiled,
                                                 'functions': functions}))
        return d

    def test_table_names_each_unit_with_public_fields_only(self):
        ep.write_unit_tables([FINDING], root=self.root)
        text = (self.root / FINDING).read_text()
        self.assertIn('| `demo-s01-demoa` | `DemoA` | `reconstruction/forms/DemoA.cpp` | `0x100` `Demo::F100` |', text)
        self.assertIn('| `demo-demob` | `DemoB` | `reconstruction/netimmerse/DemoB.cpp` | `0x200` `Demo::F200` |', text)
        # A row citing another file and a regression function stay out; no symbol or private path goes in.
        self.assertNotIn('0x300', text)
        self.assertNotIn('0x400', text)
        self.assertNotIn('?F', text)
        self.assertNotIn('.local', text)
        # The section goes before the reproduction section, the rest of the file is kept.
        self.assertLess(text.index(ep.UNIT_TABLE_HEADING), text.index('## Reproduction and sanitized evidence'))
        self.assertTrue(text.startswith(TEXT.split('## Reproduction')[0]))

    def test_regeneration_replaces_only_the_block_and_is_idempotent(self):
        self.assertEqual(ep.write_unit_tables([FINDING], root=self.root), [FINDING])
        self.assertEqual(ep.write_unit_tables([FINDING], root=self.root), [])
        self.rows[0]['name'] = 'Demo::Renamed'
        self.write_rows()
        self.assertEqual(ep.write_unit_tables([FINDING], root=self.root), [FINDING])
        text = (self.root / FINDING).read_text()
        self.assertIn('`Demo::Renamed`', text)
        self.assertNotIn('`Demo::F100`', text)
        self.assertEqual(text.count(ep.UNIT_TABLE_HEADING), 1)
        self.assertEqual(text.count(ep.UNIT_TABLE_BEGIN), 1)

    def test_a_broken_block_is_refused(self):
        (self.root / FINDING).write_text(TEXT + ep.UNIT_TABLE_BEGIN + '\n')
        with self.assertRaises(ValueError):
            ep.write_unit_tables([FINDING], root=self.root)

    def test_only_existing_findings_files(self):
        for bad in ('findings/missing.md', 'docs/x.md'):
            with self.subTest(bad=bad), self.assertRaises(SystemExit):
                ep.write_unit_tables([bad], root=self.root)

    def test_brief_names_the_evidence_file(self):
        rows = {r['id']: r for r in self.rows}
        task = json.loads((self.root / '.local/tasks/demo-s01/demo-s01-demoa/task.json').read_text())
        lines = ep.evidence_brief_lines(task, rows)
        self.assertEqual(ep.task_evidence(task, rows), [FINDING, 'findings/other.md'])
        self.assertIn(f'`{FINDING}`', lines[-1])
        self.assertEqual(ep.evidence_brief_lines(dict(task, functions=[]), rows), [])

    def test_check_labels_accepts_the_generated_table(self):
        import check_labels
        import subprocess
        checker = check_labels.Checker.__new__(check_labels.Checker)
        checker.root = self.root
        text = ('// Labels: v2\n// RVA 0x100, 8 bytes\n// Evidence: findings/demo-selection.md\n'
                'void DemoA::F100() {}\n')
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        subprocess.run(['git', 'add', FINDING], cwd=self.root, check=True)
        self.assertTrue(checker.check_evidence('reconstruction/forms/DemoA.cpp', text))
        ep.write_unit_tables([FINDING], root=self.root)
        self.assertEqual(checker.check_evidence('reconstruction/forms/DemoA.cpp', text), [])


class BriefTraits(unittest.TestCase):
    def test_adjustor_thunk_points_to_rule_25(self):
        self.assertIn('adjustor-thunk', ep.listing_traits('', {'symbol': '??_EDemo@@WBA@EAAPEAXI@Z'}))
        self.assertNotIn('adjustor-thunk', ep.listing_traits('', {'symbol': '??_GDemo@@UEAAPEAXI@Z'}))
        self.assertTrue(ep.COOKBOOK_RULES['adjustor-thunk'].startswith('25:'))


if __name__ == '__main__':
    unittest.main()
