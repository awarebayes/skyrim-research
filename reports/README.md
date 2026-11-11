# Sanitized reports

Match records, Reviewer records and the public inputs they pin: metadata, hashes and comparator
results only. No bytes, disassembly, decompiler or compiler output, objects or review prose
belong here; raw output, binaries and full reviews stay under `.local/`, never here or in Actions
artifacts. CI checks that these files agree with the integrated source and pinned metadata. It
does not compare anything with the game, and metadata validation alone does not prove that a
comparison ran.

Host names in the runs and the whole Reviewer record are self-reported by whoever wrote them;
nothing here authenticates them. The gate checks that the public files agree with each other. It
cannot show that a comparison or a review took place, or on which machine. The safeguards for
that are the sampling re-check in `docs/verification.md` (a second independent Reviewer pass and
a from-scratch comparator re-run) and git history as the audit trail.

## Layout

- `reports/<build id>/<rva>.json`: the match record for the function at that RVA, with the RVA
  lowercase hex with `0x`, as in the inventory id. The inventory entry names it in `report`.
- `reports/<build id>/<rva>.review.json`: the sanitized Reviewer record for that function. It
  exists only while the entry is `matched`; `tools/accept_function.py` writes it.
- `reports/<build id>/<rva>-recheck-cases.json`: optional supporting evidence, such as negative
  cases run alongside a re-check, with reports embedded verbatim. Not a match record; the gate
  does not read it.
- `reports/<build id>/symbol-map.json`: the symbol map the record's runs used (comparator
  contract "Mapping source symbols to target RVAs"). It holds RVAs, sizes and names from public
  community sources only, with their provenance.

## Match record (`match_record_schema` 1)

Written by `tools/verifier/match_record.py`, which refuses to write a record that
`tools/check.py` would reject. It holds:

- `function_id`: the inventory entry.
- `source`: the translation-unit files under `reconstruction/`, the compiled file, and their
  `tu-sha256-v1` digest (`tools/source_digest.py`). The files must be exactly the compiled file's
  quoted-include closure (`docs/verification.md`, "Match gate"); angle-bracket includes are
  toolchain headers bound by the toolchain pin.
- `recipe`, `toolchain_pin` (`tools/verifier/pinned.sha256`), `symbol_map`: path and SHA-256 of each.
- `reproduction`: the commands to recompile and re-run the comparison.
- `runs`: at least two comparator reports, embedded exactly as `tools/compare.py` wrote them,
  each with the host that compiled the object and the host that compared it. Runs must come
  from at least two compile hosts and two compare hosts, and runs from different compile hosts
  must name different candidate object hashes (a copied report under a second host label fails).
- `notes`: limitations, including how independent the hosts were.

Whenever an entry names a record, `tools/check.py` requires each of these to be present and
current: every pinned file's hash equals the file in the tree, and the source digest is
recomputed from the integrated files. Every report must come from the current comparator
(version and source hash), name the pinned image and the inventory's build, RVA and size, name
the integrated source digest and path and the pinned recipe, and show `pass` with full code and
unwind coverage. The comparator's `acceptance: not-evaluated` stays as written.

A change to `tools/compare.py` or `tools/pecoff.py` makes every record stale until its runs are
repeated. This is deliberate: a record vouches only for the comparator that produced it.

## Reviewer record (`review_record_schema` 1)

The public trace of the Reviewer step of the acceptance rule in `docs/verification.md`. Fields,
and no others: `function_id`, `build_id`, `rva`, `size`, `source_digest_method`,
`source_digest`, `reviewer_model`, `review_task_id`, `verdict`, `escalation_category`,
`review_sha256` (of the private review `.local/reviews/<review_task_id>.md`) and `review_date`.
`tools/check.py` requires one for every `matched` entry, with verdict `approve`, the entry's
identity and the match record's source digest. An entry is `matched` only when both records
pass; a match record alone means a reproduced pass awaiting review, not an accepted match.

## Contents

| record | function | state |
|---|---|---|
| `sse-steam-1-7-104/0x73ad90.json` | `ArmorRatingVisitor::HaveNotVisitedArmor` (COMMUNITY name) | comparator pass on 4 runs (2 compile hosts, 3 compare hosts; independence partial); Reviewer record `0x73ad90.review.json` (approve); **accepted**, entry `matched`. See `findings/first-function.md`. |
