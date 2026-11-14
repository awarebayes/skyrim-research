"""The lane's function-only policy keeps hygiene and exact-tree checks mandatory."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flow


class FunctionOnly(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='lane-policy-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.git('init', '--quiet')
        self.git('config', 'user.name', 'Synthetic')
        self.git('config', 'user.email', 'synthetic@example.invalid')
        self.write('baseline.txt')
        self.base = self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def write(self, path):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('original synthetic policy fixture\n')
        self.git('add', path)

    def commit(self):
        self.git('commit', '--quiet', '-m', 'synthetic policy fixture')
        return self.git('rev-parse', 'HEAD')

    def checks(self, commit, **kwargs):
        with patch.object(flow, 'run') as run:
            flow.pre_push_checks(self.root, commit, sys.executable, candidate=True, **kwargs)
        return [c.args[0] for c in run.call_args_list]

    def test_function_and_generated_outputs_keep_hygiene_only_locally(self):
        for path in ['reconstruction/synthetic.cpp', 'reconstruction/INDEX.md',
                     'reports/synthetic.json', 'data/progress.json', 'docs/progress.svg',
                     'docs/progress-map.svg', 'docs/model-trend.svg', 'docs/progress-trend.svg']:
            self.write(path)
        commit = self.commit()
        self.assertEqual(self.checks(commit, base_revision=self.base),
                         [[sys.executable, 'tools/check.py']])
        self.assertEqual(len(self.checks(commit)), 3, 'non-lane checks retain the full suite')

    def test_each_nonfunction_path_keeps_full_local_checks(self):
        for path in ['tools/check.py', 'tests/test_synthetic.py', '.github/workflows/check.yml',
                     'docs/verification.md', 'docs/new-site.html', 'README.md', 'data/other.json']:
            with self.subTest(path=path):
                self.git('reset', '--hard', self.base)
                self.write('reports/synthetic.json')
                self.write(path)
                commands = self.checks(self.commit(), base_revision=self.base)
                self.assertEqual(len(commands), 3)
                self.assertEqual(commands[0], [sys.executable, 'tools/check.py'])
                self.assertEqual(commands[-1], [sys.executable, 'tools/build_site.py'])

    def test_empty_diff_and_dirty_candidate_cannot_take_function_only_shortcut(self):
        self.assertFalse(flow.function_only_diff(self.root, self.base, self.base))
        self.assertEqual(len(self.checks(self.base, base_revision=self.base)), 3)
        (self.root / 'baseline.txt').write_text('changed after commit\n')
        with self.assertRaisesRegex(flow.FlowError, 'differs from its commit'):
            self.checks(self.base, base_revision=self.base)

    def test_generated_readme_totals_qualify_but_changed_prose_does_not(self):
        path = self.root / 'README.md'
        path.write_text('Synthetic prose\n<!-- model-trend-totals -->old<!-- /model-trend-totals -->\n')
        self.git('add', 'README.md')
        base = self.commit()
        path.write_text(path.read_text().replace('>old<', '>new<'))
        self.git('add', 'README.md')
        self.assertEqual(len(self.checks(self.commit(), base_revision=base)), 1)
        path.write_text(path.read_text().replace('Synthetic prose', 'Changed prose'))
        self.git('add', 'README.md')
        self.assertEqual(len(self.checks(self.commit(), base_revision=base)), 3)
        path.write_text('Synthetic prose\n<!-- model-trend-totals -->new<!-- /model-trend-totals -->\n\n')
        self.git('add', 'README.md')
        self.assertEqual(len(self.checks(self.commit(), base_revision=base)), 3,
                         'even whitespace outside generated totals keeps the full local checks')

    def test_renaming_tooling_into_reconstruction_keeps_full_local_checks(self):
        self.write('tools/synthetic.py')
        base = self.commit()
        (self.root / 'reconstruction').mkdir()
        self.git('mv', 'tools/synthetic.py', 'reconstruction/synthetic.py')
        self.assertEqual(len(self.checks(self.commit(), base_revision=base)), 3)
