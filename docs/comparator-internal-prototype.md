# Internal function comparator prototype, contract 3

Status: **prototype for independent machinery review; internal acceptance disabled**. This is
an opt-in extension in `tools/compare_internal.py`, version `0.7.0-internal-prototype`.
`tools/compare.py` and `tools/pecoff.py` remain unchanged, including their contract-2 behavior,
version and source hash. Existing schema-2 match records remain valid unchanged. The internal
engine reuses their provenance, relocation, byte, unwind, EH, funclet, TLS and overlap checks.
It adds refusals; it does not mask references or select a byte prefix.

## Candidate identity and extent

An internal task has `task_schema: 2` and `internal_identity` with exactly these fields:

- `identity_schema: 1`, `source_digest_method: "tu-sha256-v1"`, `source_revision`, `source_path`;
- `object_sha256`: this run's complete object hash, also required by the build record;
- `symbol_type: 32`, `storage_class: 3`: COFF function type and static storage;
- `section_number`, `section_name`, `entry_offset: 0`;
- `map_key`: the source-scoped identity key described below.

`symbol` remains the exact COFF spelling. Resolution requires exactly one symbol with that
spelling, type, storage, section number/name and entry offset in the hash-pinned object. A
symbol-table index is never identity. A section number is meaningful only within that pinned
object. Two same-name locals in different sections or TUs have different identities; duplicate
identical selectors fail as ambiguous.

The selected section must have initialized code and executable characteristics. Its **entire**
raw section must equal the task size. No other function-typed or external symbol may share it,
including aliases at zero. A static symbol other than its section symbol also refuses the
section. Nonzero entries, shared sections, prefixes, arbitrary subsections, scanning for bytes,
absorbed independent procedures and target funclet entries inside the primary range remain
refused. Subsequent candidate unwind entries in the primary section must be chained; the
unchanged unwind comparison checks their target counterparts. All existing EH closure and
funclet-extent checks still apply.

The claim is complete compared code and EH under these boundaries. It does not prove CRT
registration order, general referenced-data contents, startup behavior or destructor semantics.
No extra boundary proof is inferred for leaf code absent from target metadata.

## Source-scoped reference maps

The include-closure digest algorithm is unchanged: it already hashes every file's contents and
repository-relative path. New identities explicitly carry its method and digest. Changing the
source or an included header changes the identity and all local map keys.

For each defined COFF static symbol, `symbol_key(obj, sym, task)` computes a key from the JSON
array `[source_revision, source_path, symbol_name, selector]`, serialized with sorted object
keys, hashed with SHA-256, then lowercase base32 encoded without padding, split into groups of eight characters with
hyphens and prefixed `local-`. Grouping avoids a hash fragment resembling raw bytes in a report.
The selector has the five COFF fields above. The map key deliberately excludes the object hash:
clean compiles on two hosts have different object hashes, while their logical TU identities
must agree. Each run separately pins its complete object hash.

Locals outside already bound compared sections resolve **only** through those keys in the
existing schema-1 symbol map. There is no name-only fallback, even for a unique local spelling.
Symbols inside the primary or an EH-bound section retain the checked section-relative rules.
External names keep the existing rules. `atexit` and import-address slots are exact RVA entries;
TLS variables use the existing `kind: "thread-local"` entries, with source-scoped keys for
local definitions. `_tls_index` still comes from the image's TLS directory. Guards and helper
functions get the same TU scoping as other locals. Each member requires its own checked map.
Name-based automatic binding and name-only disassembly/alignment helpers are disabled for
internal attempts; explicit selector-aware mappings are required.

The internal code-section hash has prefix `internal-code-section-sha256-v1`, includes the
unchanged contract-2 section hash plus every relocation's section, offset and scoped target
key. A changed local binding identity therefore changes this hash even when its spelling is
unique. It can conservatively change for unrelated TU edits; that does not justify reusing an
approval.

## Task, runner and report schemas

Private `attempt`/`confirm` task directories use `task_schema: 2`. Each internal function adds
`internal_selector`, containing exactly the five COFF selector fields. The source revision and
per-host object hash are derived after compiling, never guessed or copied from another host.
Units containing internal selectors use `unit_spec_schema: 2`; external units keep schema 1.
Verify envelopes use `verify_task_schema: 2` for internal tasks and schema 1 for external tasks.
The flat comparator task is version 2 for internal functions. Unknown schema combinations fail.

Internal comparator reports have `report_schema: 2`, `contract_version: 3`, the internal engine's
version/source hash, and `function.internal_identity`. All other coverage, recipe, target,
source and candidate fields retain their meanings. Its source hash covers `compare.py`,
`pecoff.py`, `compare_internal.py` and `source_digest.py`. Reports stay sanitized metadata and
always say `acceptance: not-evaluated`.

`confirm` propagates each selector to both compile hosts and preserves each host's task when
re-comparing its object. `tu_task.py --internal-selector '<JSON>'` reproduces the task from the
integrated include closure and the supplied compiled object. `match_record.py` writes schema 3
for internal reports and schema 2 for external reports. Mixing engines in one record fails.

The public consistency validator checks schema-3 records against the internal engine, requires
all runs to agree on the complete identity except their per-host object hashes, and binds each
hash to that run's candidate/build facts. It keeps the existing two compile/two compare host,
source, recipe, map, full coverage, code-section and build-environment checks. Internal records
require the **exact current map hash**; additive map carry-forward is conservatively refused.
The record's function is placed through its scoped map key, not its unscoped spelling.

`validate_match` can check prototype record consistency, and confirm can assemble such records.
The public matched gate and all acceptance modes refuse schema-3 internal records pending
separate machinery and rule approval. No internal function is accepted by this prototype.

## Original synthetic fixtures and reproduction

`tests/test_compare_internal.py` creates synthetic COFF/PE inputs in memory. It covers same-name
locals, reordered symbol tables, another TU/section/object, ambiguous identity, changed source,
truncated/overlong ranges, wrong guard/atexit/import/TLS targets, reordered construction and
cleanup references, aliases/folds, EH/funclet coverage, task propagation and two-host record
consistency. No game data is present in these fixtures.

`tools/verifier/synthetic/static_identity_{a,b,runtime}.cpp` are original sources. The two
independent TUs intentionally emit identical local object/initializer/teardown spellings.
Build with the pinned toolchain, using the local runner's Wine environment and slot lock:

```sh
bash tools/verifier/build_static.sh <msvc> <new-private-output-directory>
python3 tools/verifier/static_compare.py <private-output-directory>
python3 -m unittest discover -s tests -p 'test_compare_internal.py'
```

Only the original sources and tooling are tracked. Objects, DLL, map and logs stay private.
The synthetic DLL has no CRT entry point and is never executed. Its linker map identifies
statics by both symbol spelling and object TU; no same-name lookup across TUs is used. Positive
comparisons and binding perturbations are measurements, not proof of runtime registration.

Any proposal to admit contract 3 into acceptance belongs in a separate maintainer-confirmed,
Reviewer-checked rule change. The private Engineer handoff records trial results, remaining
refusals and review questions; it is not an acceptance-rule amendment.
