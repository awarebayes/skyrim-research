# Comparator contract, version 1

Status: **draft for maintainer review.** Implemented by `tools/compare.py` (comparator version
0.1.0) with parsing in `tools/pecoff.py`, exercised by original synthetic fixtures generated
in `tests/synthetic_pecoff.py`, and run against the pinned image for the first function
(`findings/first-function.md`). A `pass` result is
evidence for review under [verification](verification.md); it is not acceptance, never sets a
function to `matched`. A `matched` status needs a match record that `tools/check.py` accepts
(`docs/verification.md`, "Match gate").

## Inputs

All inputs are local files. Each one is checked against the task before bytes are compared.

| input | contents | check |
|---|---|---|
| task | `task_id`, `build_id`, `target_image_sha256`, `rva`, `size`, `symbol`, `source_revision`, `source_path`, `recipe_sha256` | well-formed, otherwise `invalid-task` |
| target manifest | `builds/target.json` by default | `status` is `pinned` and its `build_id`/`image_sha256` equal the task's (`target-unpinned`, `manifest-mismatch`) |
| recipe | JSON naming the compiler (`binary_sha256`, `version`) and `flags` | file SHA-256 equals `task.recipe_sha256` (`stale-recipe`) |
| build record | written when the candidate was compiled: `source_revision`, `source_path`, `recipe_sha256`, `object_sha256` | equal to the task, and `object_sha256` equals the candidate object's hash (`stale-source-revision`, `source-path-mismatch`, `stale-recipe`, `object-provenance-mismatch`) |
| candidate object | x86-64 COFF object produced by the recipe | parsed per "Supported formats" |
| target image | PE32+ x86-64 image | SHA-256 equals the pinned hash (`image-hash-mismatch`) |
| symbol map | `{schema: 1, build_id, symbols: {name: {rva, size or null}}, folds: [[name, ...]]}` | same `build_id` as the task (`symbol-map-build-mismatch`) |

The comparator records the compiler hash, version and flags as given. It does not verify that
the compiler binary has that hash, that the source revision produces the object, or that the
SDK/library provenance is correct. Those belong to the verifier's build step, which writes the
build record; the comparator only proves the inputs it was handed are the ones the task pins.

## Function boundaries

- **Target:** the half-open range `[rva, rva + size)` given in the task, identified by
  `(build_id, rva, size)`. The range must lie inside one section's raw data
  (`target-range-outside-section`, `target-range-truncated`) and that section must be executable
  (`target-not-code`). The comparator does not discover boundaries; the inventory supplies them.
- **Candidate:** the task symbol must be the only definition of that name, external, at offset 0
  of an initialized code section that contains no other external or function-typed symbol at a
  non-zero offset. The function is the whole section. This is the shape MSVC emits with `/Gy`
  (one COMDAT per function). Anything else is `candidate-boundary-unsupported`.
- The candidate length must equal `size` (`function-size-mismatch`). A shorter candidate, i.e. a
  truncated function, and a task range that over-claims are both rejected; neither side is padded.
- Inter-function padding the linker inserts is outside the range and is not compared.

## Code bytes and references

Every byte in the range is compared, either exactly or as a resolved reference. The report
records both counts; `code_bytes_exact + code_bytes_by_reference` must equal `size`
(`coverage-gap`). Relocation fields are never masked:

1. All candidate relocations in the function section are validated first. Unknown or unsupported
   types fail the whole comparison (`unsupported-relocation`); fields that overlap each other or
   run past the function fail as `malformed-relocation`.
2. Bytes outside relocation fields must be identical (`code-byte-mismatch`, offset reported).
3. For each relocation, the referenced symbol is given a target RVA (next section), the field's
   inline addend is read from the candidate, and the value a linker would write is computed.
   The target's field must equal it exactly (`relocation-target-mismatch`, with type, offset and
   symbol name). Values that do not fit the field are `relocation-overflow`.

Supported relocation types:

| type | expected field |
|---|---|
| `REL32` | `S + A - (P + 4)` as signed 32-bit |
| `REL32_1` .. `REL32_5` | `S + A - (P + 4 + k)`, for an instruction with `k` immediate bytes after the field |
| `ADDR32NB` | `S + A` as unsigned 32-bit (RVA) |

`S` is the symbol's target RVA, `A` the inline addend, `P` the field's target RVA. Tests exercise
`REL32`, `REL32_1` (code) and `ADDR32NB` (`.pdata`); `REL32_2`..`REL32_5` share the `REL32_1`
code path but have no dedicated fixture.

## Mapping source symbols to target RVAs

An object file has no final placement, so placement comes from outside it:

- A symbol defined in the function's own section resolves to `task.rva + symbol offset`.
- Every other symbol, defined elsewhere in the object or undefined, is looked up **by name** in
  the symbol map for the task's build. A missing name is `unresolved-symbol`; there is no
  fallback and no guess.
- If the map lists the task symbol, its RVA and size must equal the task's (`symbol-map-conflict`).
- Absolute and debug symbols are unsupported.

Who produces the symbol map, and from which evidence (community address libraries, local
analysis), is a provenance question for the task, not something the comparator can check. A
wrong map produces `relocation-target-mismatch`, never a silent pass.

## Aliases, folds and overlaps

- A map entry other than the task symbol at the same RVA is an alias. It is accepted only when
  a `folds` group lists both names (`undeclared-alias`); declared aliases are listed in the report.
  Folded symbols in one group must share an RVA.
- A map entry that starts strictly inside the range, or whose sized range intersects it, is
  `overlapping-function`. The comparator does not reason about shared tails or multiple entries.

## Exception-related coverage (x64 `.pdata`/`.xdata`)

- Target: every `RUNTIME_FUNCTION` in the exception directory that intersects the range must lie
  entirely inside it (`unwind-entry-crosses-boundary`).
- Candidate: entries in `.pdata` sections whose begin address is relocated (`ADDR32NB`) against
  the function section. Begin and end must be in the function section and inside it.
- The `(begin, end)` offsets relative to the function start must be identical sets on both sides:
  a target entry with no candidate entry is `unwind-coverage-missing` (including a candidate with
  no `.pdata` at all); the reverse is `unwind-coverage-extra`.
- For each pair the `UNWIND_INFO` header and unwind codes (including the padding slot) must be
  identical (`unwind-info-mismatch`). The location of the unwind info itself is not compared.
- `UNWIND_INFO` other than version 1, chained entries, and entries naming an exception or
  termination handler are `unsupported-unwind`. Handler data (C++ `FuncInfo`, SEH scope tables)
  has a layout chosen by the handler, and its length cannot be derived from the unwind info.
- A range with no `.pdata` entries on either side reports `unwind: none-in-range`; that is only
  correct for a leaf function, and the report says which case applied.

## Supported formats

Fail closed (`unsupported-object-format`, `unsupported-image-format`, `truncated-input`) on:
non-x86-64 machines, `/bigobj` or anonymous object headers, objects with an optional header,
extended relocation counts, PE32 (not PE32+), and any header, table or section that extends past
the end of its input.

## Report

The public report is JSON and contains only: report schema and contract version, comparator
version and SHA-256 of its own source, task id, function identity `(build_id, rva, size, symbol)`,
source revision and path, expected and actual image hashes, candidate object hash, recipe hash,
compiler hash, version and flags, coverage counts, `result` (`pass` or `fail`), a stable `reason`
code and a short `detail`. It always has `acceptance: not-evaluated`. Before it is returned, the
comparator refuses any report that contains raw bytes or a run of 16 or more hex digits outside
hash fields. Byte-level context for a failure is written only when `--diagnostics` names a path
under `.local/`. Exit status is 0 for `pass`, 1 for `fail`, 2 for unreadable inputs.

## Explicitly unsupported in version 1

- `ADDR64`, `ADDR32`, `SECTION`, `SECREL`, `SECREL7`, `TOKEN`, `SREL32`, `PAIR`, `SSPAN32` and
  `ABSOLUTE` relocations. `ADDR64` in particular would also need the image's base relocations to be
  checked, which is not implemented.
- Functions with exception or termination handlers, separately placed funclets, chained unwind
  info, and unwind info version 2.
- Several functions per code section (non-`/Gy` objects), functions not at offset 0, hot/cold split
  functions, and secondary entry points.
- Following incremental-linking or import thunks. The map must name the exact RVA the target
  encodes, such as an import address table slot for an `__imp_` symbol.
- Jump tables and other data placed in the code range that a different relocation layout encodes.
- Checking that `.rdata` data referenced by the function has the same contents. Only addresses
  are checked, not the bytes stored there.

## Where verification.md is silent or ambiguous

These are open questions for the maintainer. The comparator takes the conservative reading
stated here; changing any of them is a contract change.

1. **"Exception-related code in the selected scope."** It does not say whether handler data,
   funclets placed apart from the parent, or IP-to-state maps are part of a function. Version 1
   compares unwind info only and refuses functions with handlers rather than shrinking scope.
2. **"Stable function RVA + length."** It does not define length. Version 1 takes length from the
   inventory and requires an exact candidate length; trailing padding is excluded. Whether the
   inventory should take length from `.pdata`, from the next function, or from analysis is open.
3. **"Alias/fold handling."** It does not say how a folded function counts for progress. The
   comparator only requires folds to be declared and lists them; counting is left to the progress
   schema change that enables `matched`.
4. **"Exact compiler binary hash, SDK/library provenance."** It does not say who verifies these.
   Here they are recorded inputs, bound to the object through the build record, and not verified.
5. **Re-check by a second host.** Proposed answer, not yet accepted: runs are recorded side by side in a
   match record (`reports/README.md`), and `tools/check.py` checks them against integrated source
   (`docs/verification.md`, "Match gate"). The comparator and report format are unchanged. A
   whole-object hash differs between clean compiles (COFF timestamp, the object path in
   `.debug$S`, and the `.chks64` checksum of that section), so each run binds its own object
   through its build record. Reproduction means every run passes against the same image from
   the same source digest and recipe; it does not mean identical objects.
6. **Referenced data.** It says data references are checked, which version 1 does as addresses
   only. Whether referenced constants must also match is not stated.
