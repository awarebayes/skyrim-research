# Finding: generated constant-return and member-return selection

Status: OBSERVED local comparator results; selection and mapping only, no accepted matches.
Author / human operator: awarebayes
AI assistance / model: Codex GPT-6.1 Sol, Engineer task p44-generator-units
Date (UTC): 2026-11-12
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size: the 372 identities in `data/generator-groups/const-return.json` and `data/generator-groups/member-return.json`
Source exposure: mixed (local binary analysis of the legally obtained pinned image, public name lists and community headers).
Sources and immutable revisions / licences: CharmedBaryon/CommonLibSSE-NG `b93280e832f263dbef44e44cbe2936622a02f91a` (MIT); meh321/AddressLibraryDatabase `0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91`, name list used with permission recorded in `docs/authorizations.md`; local function/class inventory and leaf census. No sibling implementation informed these templates.
Name provenance: COMMUNITY (unverified public association) or GUESS(low), with EXE_RTTI class attribution where available.
Confidence: high for measured counts and local comparator outcomes; medium for primary-base area attribution and public name associations; low for invented method names and inferred signatures.

## Question and method

Can conservative script-generated leaves enter the ordinary confirmation workflow with final class
paths, complete provenance labels and source bindings, without counting a single-host result as an
accepted match? The starting generator was the local lane on base `8ee2f414f6587efdc28656dac91593b945c93c40`.
Version 2 of `tools/stamp.py` writes one class pair per unit, using the documented area rules. The
family manifests record the generator version, template digest, image pin, recipe/compiler pins,
local comparator version/source hash, per-function name sources and translation-unit digests.
They describe a selection, not a family-review approval or a precommitted random sample.

Selection uses the constant-return census shapes at family ranks 11 and 22 and member-return shapes
at ranks 18 and 56. Only the explicitly decoded immediate returns and direct member loads are
emitted. Return widths and field positions are template parameters, not claims about original C++
types or declarations. Each selected class contributes one function. Existing classes, template
owners, conflicting public names, unsupported encodings and missing area rules are excluded.
Source and header paths follow `reconstruction/<area>/<Class>`; the generated files remain private
and uncommitted pending ordinary confirmation, review and integration.

A public method name is used only when its qualified spelling maps to one RVA in the local naming
inventory. Otherwise a method spelling is invented from the vtable owner and slot and labelled
`GUESS(low)`. Community names and inferred types remain unverified after a code pass. NG naming
notices are retained in both generated files. Neither the minimal class shell nor its invented
storage member names claim to reconstruct a complete class layout.

## Measured selection and local results

The corrected pilot emitted and passed 20 constant-return and 20 member-return units. Reconstruction
lint passed all 80 pilot files. The full fresh run used eight executor jobs on the verified local
Wine runner; its shared slot limit coordinated concurrent work. The runner checked its pinned
compiler binaries and target image before use. No second host was contacted.

- Constant-return: **348 emitted, 348 passed, 0 failed**; 348 functions, 1,839 bytes.
  Public names: 277 (231 meh321 and 46 NG slot); guessed names: 71.
- Member-return: **24 emitted, 24 passed, 0 failed**; 24 functions, 137 bytes.
  Public names: 12 (8 meh321 and 4 NG slot); guessed names: 12.
- Total: **372 distinct functions, 1,976 bytes**, 289 public-source names and 83 labelled guesses.
  All 372 are enrolled as `mapped`, with no match record or acceptance added.
- Real installation into a fresh scratch checkout installed all 372 pairs. `tools/check.py` passed
  there, including reconstruction lint on all 744 emitted source/header files.

Every attempt result binds the exact source closure, task identity, symbol map, recipe, image and
compiler pins, plus the selected runner configuration. Resume refuses changed or missing source
bindings or changed task inputs. Installation verifies source/index/result digests, identities and
all destination clashes before copying, and never replaces a destination file.

## Area audit and exclusions

The prior selection had 600 candidates: 162 with a prefix area and 438 without one. Of those 438,
**261 resolve mechanically**: 178 through the nearest primary base's documented prefix and 83
through an existing base class unit's area. The remaining **177 are excluded** (150 constant-return,
27 member-return). No fallback area or new layout rule was introduced. The primary-base chain is
an area inference; it is not evidence of original translation-unit membership. Alphabetical public
header paths and a census category alone do not establish an owning area.

Of the 261 inherited assignments, 51 lowercase `bhk` class owners fail the existing class-file
naming rule and are excluded without renaming them. The final 372 units comprise 162 prefix-based,
176 base-prefix and 34 base-unit assignments.
By area they are bsengine 220, forms 94, netimmerse 55, actors 2 and magic 1. The magic unit uses
an existing base's area, not a newly inferred prefix rule.

Full discovery skip counters count encountered rows, including multiple candidates for an excluded
class; they are not counts of distinct classes. Constant-return: no area rule 96, template owner
371, existing/duplicate class 157, unsupported decoding/parameters 124, conflicting name 11,
unsupported class-file spelling 140.
Member-return: no area rule 24, template owner 291, existing/duplicate class 59, unsupported
decoding/parameters 113, conflicting name 5, unsupported class-file spelling 37. These counters must not be subtracted from a different
selection's denominator or used as a project completion estimate.

## Reproduction and sanitized evidence

Use private configuration placeholders from the stamp command's help. Prepare an isolated private
checkout with the same tracked tree, recipe/pins, evidence file and access to locally held inputs.
Restrict its runner configuration to the verified local Wine attempt host. For each family:

```sh
python3 tools/stamp.py generate --config <private-config> --family <family> --out <staging>
python3 tools/stamp.py attempt --config <private-config> --out <staging> --jobs 8
python3 tools/stamp.py attempt --config <private-config> --out <staging> --jobs 8 --resume
python3 tools/stamp.py install --family <family> --from <staging> --dest <scratch-checkout>
```

The private JSONL results and pass manifest retain the measured source bindings. Public group
manifests and generated declaration symbol maps supply the identities needed for ordinary two-host
confirmation. After installing the sources in the confirmation checkout, prepare a combined brief:

```sh
python3 tools/flow.py brief confirm --manifests data/generator-groups/const-return.json data/generator-groups/member-return.json --tasks <staging-tasks>
```

This preflights every source digest, origin, task input, inventory identity and symbol binding,
then copies confirmation tasks using the public symbol maps and writes a list for the existing
`tools/verifier/confirm --list` command. It starts no host and preserves the measured attempt tasks.
The normal confirmation, per-function review and acceptance gates remain unchanged.

## Negative results, limitations and outcome

The initial pilot's 80 files failed lint because origin JSON embedded label tokens outside the v2
label grammar. The emitter was corrected, and the final pilot was freshly generated, linted and
attempted; old results were not relabelled as evidence for changed source. An intermediate full
selection passed 423 local comparisons but explicit lint found 102 path findings in 51 lowercase
class pairs. The installer refused the constant family before copying any of it. Those classes
were excluded under the unchanged lint, then both final families were generated and attempted
freshly. Negative synthetic tests
cover stale source/input bindings, wrong image, unknown areas, destination clashes and identity
errors, plus group origin/target/symbol mismatch and duplicate members.

These are local comparator passes only. No two-host reproduction, Reviewer approval, acceptance,
publication of generated units or runtime behavior validation occurred. No family-review policy
was enabled. The excluded classes need supported ownership evidence or a maintainer-reviewed
layout rule before generation; middleware needs its own provenance and licence assessment.
Reviewer: pending, under the ordinary per-function rule after two-host confirmation.
