"""The recipe-pin accessor finds the recipe script and every pin in it."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/verifier'))

import recipe_pins  # noqa: E402


class RecipePinsTest(unittest.TestCase):
    def test_recipe_script_exists_at_the_named_path(self):
        # A rename of the recipe script must update RECIPE_SCRIPT; this fails first if it does not.
        self.assertTrue((ROOT / recipe_pins.RECIPE_SCRIPT).is_file())

    def test_every_pin_is_present_and_well_formed(self):
        pins = recipe_pins.read_pins(ROOT)
        self.assertEqual(set(pins), set(recipe_pins.PIN_KEYS))
        self.assertRegex(pins['MSVC_WINE_COMMIT'], r'^[0-9a-f]{40}$')
        self.assertRegex(pins['VSMAN_SHA256'], r'^[0-9a-f]{64}$')
        self.assertTrue(pins['VSMAN_URL'].startswith('https://download.visualstudio.microsoft.com/'))
        self.assertTrue(pins['MSVC_WINE_URL'].startswith('https://'))
        self.assertRegex(pins['SDK_VERSION'], r'^10\.0\.\d+$')

    def test_missing_script_or_pin_fails_closed(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            with self.assertRaises(recipe_pins.MissingPin):
                recipe_pins.read_pins(tmp)
            script = tmp / recipe_pins.RECIPE_SCRIPT
            script.parent.mkdir(parents=True)
            script.write_text('MSVC_WINE_URL=https://example.invalid/x.git\n')
            with self.assertRaisesRegex(recipe_pins.MissingPin, 'MSVC_WINE_COMMIT'):
                recipe_pins.read_pins(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
