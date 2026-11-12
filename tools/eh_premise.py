"""Count violations of the premise the comparator's funclet-extent rules rest on, in one image.

The rules (docs/comparator-contract.md, "Exception and termination handlers") assume that code
the image's exception metadata declares as a start is never the interior of another procedure.
This measures that assumption on a whole image and prints counts only, never bytes:

- `pdata_overlaps`: pairs of `.pdata` entries whose ranges overlap;
- `entries_inside_pdata`: funclet entries (unwind actions and catch handlers of every FuncInfo
  the image's unwind info leads to) that lie strictly inside a `.pdata` range;
- `pdata_funclets_unexplained`: funclet entries with their own `.pdata` entry whose end is not a
  `.pdata` start, a funclet entry or followed by int3 padding.

All three must be 0 for the rules to hold on that image. Not measurable here: an entry inside a
leaf funclet that has no `.pdata` entry, since nothing in the image gives that funclet's extent
(the output says so in `not_measured`); the comparator's `eh-funclet-entry-inside` refuses such
an entry only inside the compared funclet itself. tests/test_eh_premise.py runs this on
the pinned image when it is available locally (SKYRIM_IMAGE, or the private export config) and
skips otherwise, so CI, which never has the image, skips it.

    python3 tools/eh_premise.py <image>
"""
import bisect
import json
from pathlib import Path
import sys

from pecoff import PeImage, Reject

COUNTS = ('pdata_overlaps', 'entries_inside_pdata', 'pdata_funclets_unexplained')


def premise_counts(image):
    """Counts for the premise checks above, plus totals for context, for a PeImage."""
    rf = sorted(image.runtime_functions())
    begins = [b for b, _e, _u in rf]
    starts = set(begins)
    entries = image.funclet_entries(None)
    overlaps = sum(1 for a, b in zip(rf, rf[1:]) if b[0] < a[1])
    inside = own = unexplained = 0
    for rva in entries:
        i = bisect.bisect_right(begins, rva) - 1
        if i < 0:
            continue
        begin, end, _u = rf[i]
        if begin < rva < end:
            inside += 1
        elif begin == rva:
            own += 1
            if end in starts or end in entries:
                continue
            pad = (-end) % 16 or 1
            try:
                following = image.read(end, pad, 'bytes after a funclet')[1]
            except Reject:
                following = b''
            if not (following and all(b == 0xCC for b in following)):
                unexplained += 1
    return {'not_measured': 'funclet entries inside leaf funclets without .pdata (no extent to test against)',
            'pdata_entries': len(rf), 'funclet_entries': len(entries), 'funclet_entries_with_pdata': own,
            'pdata_overlaps': overlaps, 'entries_inside_pdata': inside, 'pdata_funclets_unexplained': unexplained}


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    counts = premise_counts(PeImage(Path(sys.argv[1]).read_bytes()))
    print(json.dumps(counts, indent=2, sort_keys=True))
    return 0 if not any(counts[k] for k in COUNTS) else 1


if __name__ == '__main__':
    raise SystemExit(main())
