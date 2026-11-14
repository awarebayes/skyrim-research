"""Complete discovery, process isolation and failure propagation on tiny original fixtures."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'tools/test_suite.py'


class ParallelSuite(unittest.TestCase):
    def fixture(self, root, name, text):
        tests = root / 'tests'
        tests.mkdir(exist_ok=True)
        (tests / (name + '.py')).write_text(text)

    def run_suite(self, root, *args):
        return subprocess.run([sys.executable, str(RUNNER), '--root', str(root), '--jobs', '2', *args],
                              capture_output=True, text=True, timeout=30)

    def test_exact_inventory_and_module_class_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, 'test_a', '''import unittest
class T(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.seen = 0
 def test_a(self): type(self).seen += 1; self.assertEqual(self.seen, 1)
 def test_b(self): self.assertEqual(self.seen, 1)
''')
            self.fixture(root, 'test_b', 'import unittest\nclass T(unittest.TestCase):\n def test_c(self): self.assertTrue(True)\n')
            inventory = self.run_suite(root, '--list')
            self.assertEqual(sum(map(len, json.loads(inventory.stdout).values())), 3)
            run = self.run_suite(root)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('Ran 3 tests', run.stdout)
            self.assertIn('discovered 3', run.stdout)

    def test_failures_and_discovery_errors_never_go_green(self):
        for text in ('import unittest\nclass T(unittest.TestCase):\n def test_bad(self): self.fail("synthetic")\n',
                     'raise RuntimeError("synthetic import failure")\n'):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.fixture(root, 'test_failure', text)
                self.assertNotEqual(self.run_suite(root).returncode, 0)

    def test_existing_unittest_skip_is_counted_not_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, 'test_skip', 'import unittest\nclass T(unittest.TestCase):\n @unittest.skip("synthetic existing decorator")\n def test_optional(self): pass\n')
            run = self.run_suite(root)
            self.assertEqual(run.returncode, 0)
            self.assertIn('Ran 1 tests', run.stdout)
            self.assertIn('skipped=1', run.stdout)
