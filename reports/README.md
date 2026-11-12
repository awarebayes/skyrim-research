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

## Match record (`match_record_schema` 2)

Written by `tools/verifier/match_record.py`, which refuses to write a record that
`tools/check.py` would reject. It holds:

- `function_id`: the inventory entry.
- `source`: the translation-unit files under `reconstruction/`, the compiled file, and their
  `tu-sha256-v1` digest (`tools/source_digest.py`). The files must be exactly the compiled file's
  quoted-include closure (`docs/verification.md`, "Match gate"); angle-bracket includes are
  toolchain headers bound by the toolchain pin.
- `recipe`, `toolchain_pin` (`tools/verifier/pinned.sha256`), `symbol_map`: path and SHA-256 of each.
  Every run's report must give the same map SHA-256 in `symbol_map_sha256`.
- `reproduction`: the commands the compile hosts ran, with the cleared environment and the added
  `/showIncludes`, then the commands to rebuild the comparator task and re-run the comparison.
- `build`: per compile host, the flags actually passed to `cl` (recipe flags plus `added_flags`),
  the object hash, the repository files the compiler reported opening and whether they equalled
  the unit; plus the `cleared_environment` names and a `claim` stating that these facts are
  self-reported. `tools/check.py` requires the block, requires `added_flags` to be exactly
  `/showIncludes` and `cleared_environment` exactly the verifier's list, the hosts to be the
  runs' compile hosts with the runs' object hashes, and the opened files to be the unit. It cannot
  check that the facts are true. Schema 1 records had no such block and are no longer accepted.
- `runs`: at least two comparator reports, embedded exactly as `tools/compare.py` wrote them,
  each with the host that compiled the object and the host that compared it. Runs must come
  from at least two compile hosts and two compare hosts, and runs from different compile hosts
  must name different candidate object hashes (a copied report under a second host label fails).
- `notes`: limitations, including how independent the hosts were.

Per-function code-section hash: each comparator version 2 report's `candidate` block carries
`code_section_sha256` over the function's code and funclet sections, identical for every compile
of the same function code and changed by any code byte or relocation target
(`docs/comparator-contract.md`, "Report"). `tools/check.py`
requires it from every run or from none, and the runs to agree; it is what lets a delta review
show that the compared code did not change when the rest of its unit did
(`docs/verification.md`, "Stale acceptances and delta reviews").

Whenever an entry names a record, `tools/check.py` requires each of these to be present and
current: every pinned file's hash equals the file in the tree, and the source digest is
recomputed from the integrated files. Every report must come from the current comparator
(version and source hash), name the pinned image and the inventory's build, RVA and size, name
the integrated source digest and path and the pinned recipe, and show `pass` with full code and
unwind coverage. The comparator's `acceptance: not-evaluated` stays as written.

A change to `tools/compare.py` or `tools/pecoff.py` makes every record stale until its runs are
repeated. This is deliberate: a record vouches only for the comparator that produced it.

## Reviewer record (`review_record_schema` 1, 2 or 3)

The public trace of the Reviewer step of the acceptance rule in `docs/verification.md`. Schema 1
fields, and no others: `function_id`, `build_id`, `rva`, `size`, `source_digest_method`,
`source_digest`, `reviewer_model`, `review_task_id`, `verdict`, `escalation_category`,
`review_sha256` (of the private review `.local/reviews/<review_task_id>.md`) and `review_date`.
Schema 1 records are full reviews. Schema 2 adds exactly:

- `review_kind`: `full` or `delta`;
- `code_section_sha256`: the match record's per-function code-section hash (below), or `null`
  while the record carries none (full reviews only);
- for a delta review, `previous_source_digest` (the digest the superseded approval bound),
  `previous_review_sha256` (that approval's review hash) and `previous_code_section_sha256`
  (the code-section hash of the match record at that digest), which must equal
  `code_section_sha256`; all three are `null` for a full review.

`tools/accept_function.py` writes schema 3, which adds `naming_findings`: the Reviewer's
non-blocking findings on names, labels and wording (tier 2, `docs/verification.md`), a list of
short single-line strings held to a mechanical filter (no braces, code fences, private paths,
long hex runs or byte lists), empty when none are open. Schema 3 also allows `review_kind:
label-only`, written with no Reviewer pass when a re-confirmed record's code-section hash equals
the approved one ("Label-only re-acceptance"): it carries the earlier approval's reviewer model,
task id, review hash, date and naming findings (`null` if that approval predates the field), and
its `previous_review_sha256` equals its `review_sha256`.
`tools/check.py` requires one for every `matched` entry, with verdict `approve`, the entry's
identity and the match record's source digest. An entry is `matched` only when both records
pass; a match record alone means a reproduced pass awaiting review, not an accepted match.

## Contents

Per-function status is not kept here: `reconstruction/INDEX.md` is the one table, generated by
`tools/build_index.py` from `data/progress.json` and these records.
