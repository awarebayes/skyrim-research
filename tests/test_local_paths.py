"""Shared contributor storage resolves configs, source clones and caches consistently."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_labels
import check_origin
from local_paths import local_dir, local_path


class LocalPathsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'checkout'
        self.repo.mkdir()
        self.shared = self.root / 'shared'
        self.shared.mkdir()
        self.env = {'SR_LOCAL_DIR': str(self.shared)}

    def tearDown(self):
        self.tmp.cleanup()

    def test_relative_override_is_relative_to_checkout(self):
        self.assertEqual(local_dir(self.repo, {'SR_LOCAL_DIR': '../shared'}), self.shared)
        self.assertEqual(local_dir(self.repo, {}), self.repo / '.local')
        self.assertEqual(local_path(self.repo, 'reconstruction/Unit.cpp', self.env),
                         self.repo / 'reconstruction/Unit.cpp')
        self.assertEqual(local_path(self.repo, self.root / 'external', self.env), self.root / 'external')

    def test_label_and_origin_tools_use_shared_config_clones_and_cache(self):
        community = 'CharmedBaryon/CommonLibSSE-NG'
        sibling = 'momusdigital/fnv_decomp'
        (self.shared / 'verifier').mkdir()
        (self.shared / 'verifier/config.json').write_text(json.dumps({
            'community_checkouts': {community: '.local/sources/headers'},
            'sibling_checkouts': {sibling: '.local/sources/sibling'},
        }))
        for rel in ('sources/headers', 'sources/sibling'):
            (self.shared / rel).mkdir(parents=True)
        checkouts = check_labels.configured_checkouts(self.repo, self.env)
        siblings = check_labels.configured_siblings(self.repo, self.env)
        checker = check_labels.Checker(checkouts, self.repo, siblings, env=self.env)
        self.assertEqual(checker.checkouts[community], self.shared / 'sources/headers')
        self.assertEqual(checker.siblings[sibling], self.shared / 'sources/sibling')
        with patch.object(check_origin, 'Clone') as clone:
            check_origin.open_clones(self.repo, env=self.env)
        opened = {c.args[0]: c.args for c in clone.call_args_list}
        self.assertEqual(opened[community][1], self.shared / 'sources/headers')
        self.assertEqual(opened[sibling][1], self.shared / 'sources/sibling')
        self.assertTrue(all(args[-1] == self.shared / 'analysis/origin-index' for args in opened.values()))
        self.assertFalse((self.repo / '.local').exists())


if __name__ == '__main__':
    unittest.main()
