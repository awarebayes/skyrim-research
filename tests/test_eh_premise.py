"""The funclet-extent premise (tools/eh_premise.py): synthetic checks, and the pinned image when present."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from eh_premise import COUNTS, premise_counts  # noqa: E402
from pecoff import PeImage  # noqa: E402
import synthetic_pecoff as fx  # noqa: E402


def pinned_image():
    """Bytes of the pinned target if this machine has it, else None (CI never does)."""
    candidates = [os.environ.get('SKYRIM_IMAGE')]
    config = ROOT / '.local/config/export_pack.json'
    if config.is_file():
        candidates.append(json.loads(config.read_text()).get('image'))
    pinned = json.loads((ROOT / 'builds/target.json').read_text()).get('image_sha256')
    for path in filter(None, candidates):
        path = Path(path)
        if path.is_file():
            blob = path.read_bytes()
            if hashlib.sha256(blob).hexdigest() == pinned:
                return blob
    return None


class SyntheticPremiseTests(unittest.TestCase):
    def test_packed_fixture_holds_the_premise(self):
        counts = premise_counts(PeImage(fx.packed_image(fx.packed_unit())))
        self.assertEqual({k: counts[k] for k in COUNTS}, dict.fromkeys(COUNTS, 0))
        self.assertGreaterEqual(counts['funclet_entries'], 2)

    def test_entry_inside_a_pdata_range_is_counted(self):
        # A FuncInfo naming an address inside the compared parent's own .pdata range.
        unit = fx.packed_unit()
        patches, extra = fx.fake_funcinfo([fx.section_rva(unit, fx.PACKED_FUNCTION) + 4])
        counts = premise_counts(PeImage(fx.packed_image(unit, patches=patches, extra_pdata=extra)))
        self.assertEqual(counts['entries_inside_pdata'], 1)

    def test_overlapping_pdata_is_counted(self):
        unit = fx.packed_unit()
        start = fx.section_rva(unit, fx.PACKED_FUNCTION)
        unwind = fx.section_rva(unit, f'$unwind${fx.PACKED_FUNCTION}')
        image = fx.packed_image(unit, extra_pdata=((start + 2, start + 6, unwind),))
        self.assertEqual(premise_counts(PeImage(image))['pdata_overlaps'], 1)

    def test_funclet_pdata_end_without_boundary_is_counted(self):
        frame = fx.FRAME_FUNCLET
        unit = fx.packed_unit(funclet_code=frame, funclet_pdata=(0, len(frame) - 1, fx.FRAME_FUNCLET_UNWIND),
                              neighbor_magic=0x19930521)
        self.assertEqual(premise_counts(PeImage(fx.packed_image(unit)))['pdata_funclets_unexplained'], 1)


@unittest.skipUnless(pinned_image() is not None, 'pinned target image not available on this machine')
class PinnedImagePremiseTests(unittest.TestCase):
    def test_premise_holds_on_the_pinned_image(self):
        counts = premise_counts(PeImage(pinned_image()))
        self.assertEqual({k: counts[k] for k in COUNTS}, dict.fromkeys(COUNTS, 0), counts)


if __name__ == '__main__':
    unittest.main()
