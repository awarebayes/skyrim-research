# Comparator contract, version 2

Status: **draft for maintainer review.** Implemented by `tools/compare.py` (comparator version
0.2.0) with parsing in `tools/pecoff.py`, exercised by original synthetic fixtures generated
in `tests/synthetic_pecoff.py` and by real MSVC output of original synthetic sources
(`tools/verifier/synthetic/eh_cases.cpp`, `eh_gs.cpp`), and run against the pinned image for
the accepted functions. Version 2 adds exception and termination handlers with their data and
funclets, chained unwind info and several `.pdata` entries per function, and makes jump tables
explicit; everything version 1 compared is compared the same way. A `pass` result is evidence under
[verification](verification.md); it is not acceptance and never sets a function to `matched`.
A `matched` status needs a match record and a Reviewer `approve` record that `tools/check.py`
accepts (`docs/verification.md`, "Acceptance rule" and "Match gate").

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
- The function section holds everything MSVC puts in it: the code covered by the primary
  `.pdata` entry, the code covered by chained entries after it, and jump tables placed after the
  code. So `size` is the whole section, which can be larger than the primary `.pdata` entry
  (measured with MSVC 19.16: a function whose later entries chain to the first has all of them
  contiguous in one section). An inventory that takes `size` from the primary entry alone gets
  `function-size-mismatch` for such functions, never a partial pass.
- **Funclets** (catch blocks, unwind actions, SEH filters and `__finally` blocks) are separate
  code sections in the object (`.text$x`, several funclets may share one) and are placed apart
  from the parent in the image. They are part of the function: see "Exception and termination
  handlers". They are compared in full but reported separately from `size`, which stays the
  inventory's primary range.
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
`REL32`, `REL32_1` (code), `ADDR32NB` (`.pdata`, EH data, jump tables); `REL32_2`..`REL32_5`
share the `REL32_1` code path but have no dedicated fixture.

### Jump tables

MSVC x64 places a switch's table in the function's own section after the code: an array of
`ADDR32NB` entries against labels in the same section, read by an instruction whose
displacement is an `ADDR32NB` against the table's label and based on `lea reg, [__ImageBase]`
(`REL32` against `__ImageBase`). Every entry is therefore an ordinary relocation in the range and
is compared as one: each entry must encode exactly `task.rva + label offset`, so a table that
sends any case to another target fails as `relocation-target-mismatch`. `__ImageBase` is the
linker-defined image base and resolves to RVA 0 without a map entry; a map that gives it another
RVA is `symbol-map-conflict`. The report counts `ADDR32NB` fields whose symbol lies in the
function's own section as `self_rva_fields`. Tables placed outside the section (not seen from
MSVC 19.16) would reference another section and need the map, like any data.

## Mapping source symbols to target RVAs

An object file has no final placement, so placement comes from outside it:

- A symbol defined in the function's own section resolves to `task.rva + symbol offset`.
- A symbol in a section **bound** by the exception data (funclet code, handler data; see below)
  resolves to that section's bound RVA plus the symbol offset. Binding happens only through a
  compared field and every bound section is compared in full, so no placement is taken on trust.
- `__ImageBase` resolves to 0 (see "Jump tables").
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

## Unwind coverage (x64 `.pdata`/`.xdata`)

- The function's code sections are the function section plus every funclet section bound by its
  exception data. For each code section with target range `[start, end)`:
  - every target `RUNTIME_FUNCTION` that intersects the range must lie entirely inside it
    (`unwind-entry-crosses-boundary`);
  - candidate entries are those in `.pdata` sections whose begin address is relocated
    (`ADDR32NB`) against that section; begin and end must lie in it;
  - the `(begin, end)` offsets relative to the section start must be identical sets on both
    sides: a target entry with no candidate entry is `unwind-coverage-missing` (including a
    candidate with no `.pdata` at all); the reverse is `unwind-coverage-extra`. Entries on
    either side must not overlap or repeat (`unwind-entry-overlap`), so every entry is
    compared exactly once.
- For each pair the unwind info is compared as below. The location of a primary entry's unwind
  info is not compared (it is reached through the compared `.pdata` entry); its content is.
- A range with no `.pdata` entries on either side reports `unwind: none-in-range`; that is only
  correct for a leaf function, and the report says which case applied.

### Unwind info

- Version must be 1 (`unsupported-unwind` for version 2 or anything else). The header and all
  unwind codes, including the padding slot, must be identical (`unwind-info-mismatch`), and no
  relocation may fall inside them (`unsupported-relocation`).
- `UNW_FLAG_CHAININFO`: the `RUNTIME_FUNCTION` after the codes names the parent. Its begin and
  end are resolved from the candidate's relocations and must equal the target's
  (`unwind-chain-mismatch`); its unwind-info field binds or checks the parent's unwind info,
  which is compared in turn. A chain flag combined with a handler flag is `unsupported-unwind`.
- `UNW_FLAG_EHANDLER`/`UNW_FLAG_UHANDLER`: the handler RVA after the codes must be relocated
  against an undefined symbol and equal that symbol's RVA from the map (`eh-handler-mismatch`).
  The handler's name selects the data layout below; any other name, a handler defined in the
  candidate object, and `__CxxFrameHandler4` (not used by the pinned image, measured) are
  `unsupported-eh-handler`.

## Exception and termination handlers

Handler data has a layout chosen by the handler. Version 2 decodes the layouts below; anything
else is rejected, never skipped.

| handler | data after the handler RVA |
|---|---|
| `__CxxFrameHandler3` | RVA of a `FuncInfo` |
| `__GSHandlerCheck_EH` | RVA of a `FuncInfo`, then GS data |
| `__C_specific_handler` | scope table |
| `__GSHandlerCheck_SEH` | scope table, then GS data |
| `__GSHandlerCheck` | GS data |

Structures (x64, all fields 4 bytes):

| structure | fields |
|---|---|
| `FuncInfo` | magic, maxState, unwind map, nTryBlocks, try-block map, nIPMapEntries, IP-to-state map, dispUnwindHelp, ES type list, EHFlags |
| unwind map entry | toState, action (code, may be null) |
| try-block map entry | tryLow, tryHigh, catchHigh, nCatches, handler array |
| handler type | adjectives, type descriptor (may be null for `catch (...)`), dispCatchObj, handler (code), dispFrame |
| IP-to-state entry | IP (code), state |
| ES type list | nCount, handler type array |
| scope table | count, then per entry begin (code), end (code), handler (code or constant), jump target (code or 0) |
| GS data | cookie offset with flags in the low 3 bits; with flag 4 also aligned base offset and alignment |

Only `FuncInfo` magic `0x19930522` (the value MSVC 19.16 emits, measured) is decoded; others are
`eh-funcinfo-unsupported`. Arrays are read with the counts compared just before them.

How every field is compared, on the candidate side from the object's bytes and relocations and on
the target side from the image at the bound RVA:

- **Integer fields** (counts, states, displacements, flags, magic, GS data, constant scope
  handlers): no relocation may fall on them (`eh-unexpected-relocation`) and the values must be
  equal (`eh-data-mismatch`, naming structure and field).
- **Reference fields** relocated with `ADDR32NB` (any other type is `unsupported-relocation`):
  - against a symbol in the function section or an already bound section: the target field must
    equal that section's RVA plus symbol offset plus addend (`eh-reference-mismatch`);
  - against a static symbol in an unbound section of the object (handler data, funclets): the
    section is **bound** at the RVA the target field holds, minus the symbol offset and addend.
    A section can be bound once; a second reference must agree (`eh-reference-mismatch`).
    Structure fields must bind data sections and code fields code sections
    (`eh-reference-kind`);
  - against anything else (type descriptors, external symbols): resolved through the map
    like code references; a mismatch is `eh-reference-mismatch`.
- **Unrelocated reference fields** must be 0 on both sides (null pointer or `catch (...)`); a
  non-zero unrelocated reference is `eh-unrelocated-reference`.
- **Type descriptors** of catch handlers: when the candidate object defines the descriptor, its
  decorated type name (the bytes from offset 16 to the end of its section) must also equal the
  target's bytes at the resolved RVA (`eh-catch-type-mismatch`). The name is compared, never
  reported.

Completeness, so nothing is skipped:

- Every bound data section must be claimed byte for byte by decoded structures, each byte once,
  and every relocation in it must be consumed by a reference field (`eh-data-unaccounted`,
  `eh-data-overlap`). Structures reached twice (a funclet's unwind info points to its parent's
  `FuncInfo`) are compared once.
- Every bound code section is a funclet: its target range must lie in an executable section,
  must not overlap the function or another funclet (`eh-funclet-overlap`) or a sized map entry
  (`overlapping-function`), and is compared exactly like the function: every byte exactly or as a
  resolved relocation, its `.pdata` entries as above, their unwind info and handler data as here.
- The report counts funclet sections and bytes (`funclet_bytes_exact` plus
  `funclet_bytes_by_reference` must equal `funclet_bytes_total`, otherwise `coverage-gap`),
  structures by kind, reference and integer fields, and compared type names.

What this establishes: the target's handler, every state transition, try range, catch type,
catch-object and frame displacement, IP-to-state boundary and funclet equals what the candidate
compiles to. What it does not: the contents of type descriptors beyond their names, the handler
routines themselves (CRT code reached through the map) and `.rdata` contents referenced from
funclets (addresses only, as for the function).

## Supported formats

Fail closed (`unsupported-object-format`, `unsupported-image-format`, `truncated-input`) on:
non-x86-64 machines, `/bigobj` or anonymous object headers, objects with an optional header,
extended relocation counts, PE32 (not PE32+), and any header, table or section that extends past
the end of its input.

## Report

The public report is JSON and contains only: report schema and contract version, comparator
version and SHA-256 of its own source, task id, function identity `(build_id, rva, size, symbol)`,
source revision and path, expected and actual image hashes, candidate object hash and code
section hash (below), recipe hash,
compiler hash, version and flags, coverage counts, `result` (`pass` or `fail`), a stable `reason`
code and a short `detail`. It always has `acceptance: not-evaluated`.

`candidate.code_section_sha256` (`code-section-sha256-v1`) identifies the compared code
independently of the object file around it, so it is identical across clean compiles of the same
source and recipe, unlike `object_sha256`. It is SHA-256 over a fixed prefix, the number of
sections, then per section in order: name length and section length, name, section bytes, the
relocation count, and each relocation sorted by offset as offset, type and the target symbol's
**name** (never its symbol-table index). The sections are the function section first, then the
funclet sections in the order the exception data bound them (unwind walk of the function's
`.pdata` entries in address order, structures field by field). `candidate.code_sections` gives
their number. The object time stamp, symbol-table order and every other section stay out of it;
any code byte, padding byte inside a section or relocation target changes it. It is present
whenever the task symbol was found; in a failing report it covers the sections bound before the
failure. Before it is returned, the
comparator refuses any report that contains raw bytes or a run of 16 or more hex digits outside
hash fields. Byte-level context for a failure is written only when `--diagnostics` names a path
under `.local/`. Exit status is 0 for `pass`, 1 for `fail`, 2 for unreadable inputs.

## Explicitly unsupported in version 2

- `ADDR64`, `ADDR32`, `SECTION`, `SECREL`, `SECREL7`, `TOKEN`, `SREL32`, `PAIR`, `SSPAN32` and
  `ABSOLUTE` relocations. `ADDR64` in particular would also need the image's base relocations to be
  checked, which is not implemented.
- Unwind info version 2; `__CxxFrameHandler4` and its compressed data; `FuncInfo` magic other
  than `0x19930522`; any other language-specific handler.
- Several functions per code section (non-`/Gy` objects), functions not at offset 0, hot/cold
  split functions whose parts are separate sections, chained entries outside the function's own
  section, and secondary entry points.
- Following incremental-linking or import thunks. The map must name the exact RVA the target
  encodes, such as an import address table slot for an `__imp_` symbol. A thunk is compared like
  any function if the inventory gives it a range and the candidate defines it; the comparator has
  no thunk-specific rule.
- Data placed in the code range by a layout other than the jump tables above.
- Checking that `.rdata` data referenced by the function has the same contents. Only addresses
  are checked, not the bytes stored there.

## Where verification.md is silent or ambiguous

These are open questions for the maintainer. The comparator takes the conservative reading
stated here; changing any of them is a contract change.

1. **"Exception-related code in the selected scope."** It does not say whether handler data,
   funclets placed apart from the parent, or IP-to-state maps are part of a function. Version 2
   takes the widest reading: all of them are, and all are compared. Funclet bytes are reported
   apart from `size`, which remains the primary range; whether progress should count them is
   left to the progress schema.
2. **"Stable function RVA + length."** It does not define length. Version 1 takes length from the
   inventory and requires an exact candidate length; trailing padding is excluded. Whether the
   inventory should take length from `.pdata`, from the next function, or from analysis is open.
3. **"Alias/fold handling."** It does not say how a folded function counts for progress. The
   comparator only requires folds to be declared and lists them; counting is left to the progress
   schema change that enables `matched`.
4. **"Exact compiler binary hash, SDK/library provenance."** It does not say who verifies these.
   Here they are recorded inputs, bound to the object through the build record, and not verified.
5. **Re-check by a second host.** Answered by the match gate, which as a machinery change still
   needs its own Reviewer pass under the acceptance rule: runs are recorded side by side in a
   match record (`reports/README.md`), and `tools/check.py` requires at least two compile hosts
   and two compare hosts and checks every run against integrated source (`docs/verification.md`,
   "Match gate"). The comparator and report format are unchanged. A
   whole-object hash differs between clean compiles (COFF timestamp, the object path in
   `.debug$S`, and the `.chks64` checksum of that section), so each run binds its own object
   through its build record. Reproduction means every run passes against the same image from
   the same source digest and recipe; it does not mean identical objects. Version 2 adds report
   fields (funclet and EH counts) and new reason codes; the match gate needs no change because a
   `pass` still implies complete coverage and the gate checks the same fields as before.
6. **Referenced data.** It says data references are checked, which versions 1 and 2 do as addresses
   only. Whether referenced constants must also match is not stated.
