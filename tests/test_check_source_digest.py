"""The check's cache must preserve the source-digest implementation's results."""
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import check_source_digest as cached
import source_digest as reference


class CachedClosureTests(unittest.TestCase):
    def test_fixture_closures_and_digests_match_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {
                'src/a.cpp': '#include "shared.h"\n',
                'src/b.cpp': '#include "shared.h"\n',
                'src/shared.h': '#include "nested/leaf.h"\n',
                'src/nested/leaf.h': '#include "shared.h"\n',
                'reconstruction/other.h': '// header\n',
                'src/c.cpp': '#include <other.h>\n',
            }
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            with cached.source_digest_cache():
                for name in ('src/a.cpp', 'src/b.cpp', 'src/c.cpp'):
                    for roots in (None, ()):
                        expected = reference.include_closure(root, name, roots)
                        actual = cached.include_closure(root, name, roots)
                        self.assertEqual(actual, expected)
                        self.assertEqual(reference.tu_digest(root, actual), reference.tu_digest(root, expected))
                        self.assertEqual(cached.include_closure(root, name, roots), expected)

    def test_cache_is_discarded_between_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a.cpp').write_text('#include "x.h"\n')
            (root / 'x.h').write_text('')
            with cached.source_digest_cache():
                cached.include_closure(root, 'a.cpp')
            (root / 'x.h').unlink()
            with cached.source_digest_cache():
                with self.assertRaises(ValueError):
                    cached.include_closure(root, 'a.cpp')
