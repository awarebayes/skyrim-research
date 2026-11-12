# Comparator contract, version 2

Status: **draft for maintainer review.** Implemented by `tools/compare.py` (comparator version
0.5.0) with parsing in `tools/pecoff.py`, exercised by original synthetic fixtures generated
in `tests/synthetic_pecoff.py` and by real MSVC output of original synthetic sources
(`tools/verifier/synthetic/eh_cases.cpp`, `eh_gs.cpp`), and run against the pinned image for
the accepted functions. Version 2 adds exception and termination handlers with their data and
funclets, chained unwind info and several `.pdata` entries per function, and makes jump tables
explicit; everything version 1 compared is compared the same way. Comparator 0.5.0 adds
thread-local variables (`SECREL` against a declared TLS-template offset, `_tls_index` from the
TLS directory) within contract version 2; see "Thread-local variables" and "Versions and earlier
results". A `pass` result is evidence under
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
| symbol map | `{schema: 1, build_id, symbols: {name: entry}, folds: [[name, ...]]}`; an entry is `{rva, size or null}` (code or data) or `{kind: "thread-local", tls_offset, size or null}` | same `build_id` as the task (`symbol-map-build-mismatch`); entry shape (`invalid-symbol-map`); thread-local entries against the image's TLS directory ("Thread-local variables") |

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
| `SECREL` | `T + A` as unsigned 32-bit, in code only, against a thread-local variable (below) |

`S` is the symbol's target RVA, `A` the inline addend, `P` the field's target RVA, `T` the
variable's declared offset in the image's TLS template. Tests exercise `REL32`, `REL32_1` (code),
`ADDR32NB` (`.pdata`, EH data, jump tables) and `SECREL` (code); `REL32_2`..`REL32_5` share the
`REL32_1` code path but have no dedicated fixture. `SECREL` is accepted only in the function's
and funclets' code; in `.pdata`, unwind info or EH data it stays `unsupported-relocation`.

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

### Thread-local variables

MSVC x64 reads a `__declspec(thread)` variable (and the thread-safe-statics epoch
`_Init_thread_epoch`, which is one) as: load `_tls_index` (`REL32`), read the TLS array at
`gs:[0x58]` (plain bytes), index it, then address the variable at a 32-bit displacement relocated
with `SECREL`. For a symbol in the TLS template the MSVC 19.16 linker writes that field as the
symbol's offset from the template start, which is its offset in every thread's TLS block
(measured on `tools/verifier/synthetic/tls_cases.cpp`: the linker merged the template into
`.rdata` at a non-zero section offset, and every field equalled the symbol's map address minus
`StartAddressOfRawData`, not minus the section start). The instruction bytes around the field
are compared exactly, so the access pattern is the candidate's; only the two references need
rules.

Image side. The TLS directory (data directory 9, `IMAGE_TLS_DIRECTORY64`) is read only when the
map has a thread-local entry or a `_tls_index` entry, or the candidate references `_tls_index`
or uses `SECREL`; a missing directory then is `tls-directory-missing`. It must be at least 40
bytes and readable; `StartAddressOfRawData`, `EndAddressOfRawData` and `AddressOfIndex` are
virtual addresses and become RVAs by subtracting the image base; start must not exceed end and
the template start and the index slot must lie in a section (`malformed-tls-directory`). The
template `[start, end)` must end inside the section it starts in (`unsupported-tls-layout`).
`SizeOfZeroFill`, the callbacks and the characteristics are not used: an offset in the zero-fill
area is rejected like any offset outside `[0, end - start)`.

Map side. A thread-local variable has an entry of its own kind, never an RVA:

```json
"?tGuard@@3HA": {"kind": "thread-local", "tls_offset": 1896, "size": 4}
```

`tls_offset` is the offset from the template start, `size` the variable's size or null. Such an
entry must not carry `rva`; any other `kind` is `invalid-symbol-map`. Every thread-local entry
is checked against the template before code is compared: `tls_offset + max(size, 1)` must not
exceed the template size (`tls-offset-outside-template`). Thread-local entries take no part in
placement, alias, fold or overlap checks, which concern RVAs; a fold or the task symbol naming one
is `invalid-symbol-map` or `symbol-map-conflict`.

Code side, for each `SECREL` field:

- the referenced symbol is resolved **by name** through a thread-local map entry only. A symbol
  missing from the map is `unresolved-symbol`; one whose entry is an RVA entry is
  `unsupported-relocation` (`SECREL` to something that is not thread-local);
- the candidate symbol must be undefined (an `extern __declspec(thread)` declaration) or defined
  in a candidate section named `.tls` or `.tls$...`; a symbol in any other section, a section
  symbol, or an absolute or debug symbol is `unsupported-relocation`. The candidate's own offset
  in its `.tls$` section is never used: placement comes from the map, as for any data;
- the inline addend `A` is read as unsigned 32-bit; with a sized entry it must be less than
  `size`, and in every case `T + A` must lie inside the template (`tls-offset-outside-template`);
- the target field must equal `T + A` exactly (`relocation-target-mismatch`). The comparator
  never derives `T` from the target's displacement.

Any other relocation type against a thread-local entry is `tls-reference-kind`. `_tls_index`,
when undefined in the candidate, resolves to `AddressOfIndex` minus the image base and needs no
map entry; a map entry for it must give that RVA (`tls-index-mismatch`), and a map that declares
it thread-local is `invalid-symbol-map`. A candidate that defines `_tls_index` itself is
`unsupported-relocation` on any reference to it.

What this establishes: the function reads and writes the same TLS-template offsets, through the
same index slot, as the target, and the candidate names each offset with the variable the map
declares there. What it does not: the template's initial contents (as for `.rdata`, addresses
only), the candidate's `.tls$` bytes, the size of the template, TLS callbacks or dynamic
initializers of `thread_local` objects (ordinary functions, compared only if the inventory gives
them a range), and whether two map names share one offset (not checked, as for data RVAs).

Where the offset comes from. A thread-local entry, like a data RVA bound by position, is read
from the target's own code (the constant it adds to the TLS block), so for one function it is
not independent evidence of identity; what the comparison adds is that one map entry serves every
function using that name, so all of them must agree on it. Drafters do not edit the map: a bind
hint `"<decorated name>": "tls:0x<offset>"` makes `tools/verifier/bind.py` write the entry
(`bind.py` never binds a `SECREL` reference by position or community name), and integration
copies it to the repository map like any other entry.

Measured proof (`tools/verifier/build_tls.sh`, `tools/verifier/tls_compare.py`, pinned compiler
and linker on the standing verifier machine, compared there and on macOS with identical
summaries): a plain read, a two-variable update, a struct member, a thread-safe static
(`_Init_thread_epoch`) and a catch funclet reading a thread-local all pass; the perturbed
`tls_variant.cpp` (same functions reading another variable or member) and altered maps and images
(wrong offset, offset outside the template, missing entry, entry given as an RVA, `_tls_index`
entry or directory slot moved, no TLS directory) all fail with the reasons above. The pinned
target image has the same layout as the synthetic DLL: one TLS directory, its template inside
`.rdata` but not at its start, no zero-fill.

## Mapping source symbols to target RVAs

An object file has no final placement, so placement comes from outside it:

- A symbol defined in the function's own section resolves to `task.rva + symbol offset`.
- A symbol in a section **bound** by the exception data (funclet code, handler data; see below)
  resolves to that section's bound RVA plus the symbol offset. Binding happens only through a
  compared field and every bound section is compared in full, so no placement is taken on trust.
- `__ImageBase` resolves to 0 (see "Jump tables"); an undefined `_tls_index` resolves to the
  image's TLS index slot, and a `SECREL` symbol to its thread-local entry's offset (see
  "Thread-local variables").
- Every other symbol, defined elsewhere in the object or undefined, is looked up **by name** in
  the symbol map for the task's build. A missing name is `unresolved-symbol`; there is no
  fallback and no guess.
- If the map lists the task symbol, its RVA and size must equal the task's (`symbol-map-conflict`).
- Absolute and debug symbols are unsupported.

Who produces the symbol map, and from which evidence (community address libraries, local
analysis), is a provenance question for the task, not something the comparator can check. A
wrong map produces `relocation-target-mismatch`, never a silent pass.

The comparator reads the whole map: the names it resolves, and also the absence of entries at or
inside the function and funclet ranges, of an entry naming the task symbol elsewhere, of
`__ImageBase`, of `_tls_index` (checked against the TLS directory's slot whenever present), of
any thread-local entry (each is checked against the image's TLS template, and the first makes a
TLS directory required), and of the EH handler names. A result
therefore depends on more than the resolved entries, which is why the matching gate
(`docs/verification.md`, "Symbol map") carries a record across map additions only when none of
them could have touched those checks, and never across a change to an entry the pinned version
held. The repository map is changed only with `tools/symbol_map.py`.

### Symbol map dependences

Every place `tools/compare.py` reads the map, the rule in `carry_forward_problem`
(`tools/symbol_map.py`) or elsewhere in the gate that covers it, and the tests showing it.
`MapReadingGuardTests` in `tests/test_symbol_map.py` fingerprints the functions named here and
fails when they change or another function reads the map; a failure means re-checking this
table against the new code before updating the fingerprint. Tests are in `test_symbol_map.py`
unless named otherwise.

| where | what the result depends on | covering rule | tests |
|---|---|---|---|
| `compare()`, map handling | map bytes hashed into `symbol_map_sha256`; non-JSON fails | the record pin must equal every run's hash (check.py); versions rebuild from the current map | `test_match_gate`: `test_report_from_another_map_rejected`, `test_report_without_map_hash_rejected`, `test_stale_symbol_map_rejected` |
| `load_symbol_map`, top level | `schema`, `build_id`, `symbols` object | top-level keys are copied verbatim when a version is rebuilt, so any change breaks the rebuild; `check_map` runs on every map written | `ForgedHistoryTests`, `test_whitespace_change_fails` |
| `load_symbol_map`, entries | size null or positive; RVA entry needs an unsigned `rva`; only kind `thread-local`, with unsigned `tls_offset`, no `rva`, not named `_tls_index` | `check_map` on every map; `incoming_entry`; one spelling per entry (`{rva, size}` or `{kind, tls_offset, size}`, in that order); an added entry of unknown kind stales | `test_malformed_thread_local_entry_is_refused`, `test_rva_entry_needs_exactly_rva_and_size`, `test_unknown_entry_kind_is_not_carried`, `test_every_entry_kind_has_a_rule` |
| `load_symbol_map`, folds | groups list RVA entries sharing an RVA | a new fold group naming existing names is a change; `check_map` | `test_extended_fold_group_supersedes`, `test_added_entries_sharing_rva_need_a_fold` |
| `check_tls`, trigger | runs if any thread-local entry or `_tls_index` is present, and then needs a TLS directory | any thread-local addition stales; a `_tls_index` addition stales | `test_thread_local_addition_makes_record_stale`, `test_tls_index_addition_makes_record_stale` |
| `check_tls`, template bound | every thread-local entry lies inside the TLS template | any thread-local addition stales; a change or removal supersedes | `test_second_thread_local_entry_stales`, `test_changed_thread_local_entry_stales`, `test_resized_thread_local_entry_stales`, `test_removed_thread_local_entry_stales` |
| `check_tls`, `_tls_index` | its RVA equals the directory's index slot | a `_tls_index` addition stales and `add` refuses it without `--allow-change` | `test_tls_index_addition_is_refused_and_lists_the_record`, `test_tls_index_addition_is_refused_without_any_record` |
| `check_placement`, kind | the task symbol is not thread-local | thread-local additions stale; an addition named as the function stales | `test_function_name_added_elsewhere_is_not_carried` |
| `check_placement`, `__ImageBase` | absent or at RVA 0 | an `__ImageBase` addition stales and `add` refuses it without `--allow-change` | `test_image_base_addition_makes_record_stale`, `test_each_presence_name_is_not_carried` |
| `check_placement`, task entry | an entry for the task symbol has the task RVA and size | addition named as the function stales; check.py requires the current entry to match the inventory range | `test_function_name_added_elsewhere_is_not_carried`, `test_addition_at_function_makes_record_stale_even_when_forced` |
| `check_placement`, aliases and overlap | an entry at the start needs a fold; none may start inside or intersect the range | an addition at or in the range stales (`overlaps`, a superset of the comparator's test) | `test_addition_at_function_makes_record_stale_even_when_forced`, `test_addition_overlapping_function_makes_record_stale` |
| `Function.resolve` | `_tls_index` comes from the image and undefined `__ImageBase` is 0, not from the map; a name in the thread-local entries is `tls-reference-kind`; any other name must be an RVA entry | a pass resolved no name its version lacked (`unresolved-symbol`); a change supersedes | `test_changed_entry_with_flag_makes_record_stale` |
| `Function.secrel_field` | the name is thread-local and not an RVA entry; offset plus addend inside the variable and template | as `resolve`; a thread-local change supersedes | `test_changed_thread_local_entry_stales` |
| `Function.bind` | no RVA entry starts in or intersects a funclet it binds | an addition at or in a funclet range the reports give stales; reports whose ranges are not identical across runs, integer-counted, complete and disjoint carry across nothing | `FuncletCarryForwardTests` |
| `Function.check_target_closure` | which RVA entries name a FuncInfo-based EH handler | an EH handler addition stales when the function has handler data | `test_eh_handler_addition_with_handler_data_is_not_carried`, `test_each_presence_name_is_not_carried` |

Other references (handler names in exception data, type descriptors) go through
`Function.resolve`. `check_funclet_end` takes boundaries from `.pdata` and the compared code
ranges, never from map entries.

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
  - only the language handler and catch type descriptors are resolved through the map (by
    name, like code references; a mismatch is `eh-handler-mismatch` or `eh-reference-mismatch`).
    Every other reference field (structure arrays, the ES type list, unwind actions, catch
    handlers, IP-to-state addresses, scope begin/end/handler/target, chained begin/end and parent)
    must be relocated against a section of this object that is or becomes bound, and so is
    compared in full. One relocated against an external or undefined symbol is
    `eh-reference-not-local`: whatever the map names there would never be compared.
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
- A funclet's length comes from its candidate section. Funclets with `.pdata` are bounded by
  their entries; one without (MSVC emits unwind funclets without `.pdata`) has no target-side
  length. So the target must show a boundary right after every bound funclet section: a target
  `.pdata` entry, the function or another compared funclet starts there, or the bytes from there
  to the next 16-byte boundary (at least one byte) are `int3` padding, which the MSVC linker puts
  between code sections. Otherwise `eh-funclet-extent`. Candidate-side facts are not boundaries:
  a symbol-map entry at that address names nothing the target shows, and an EH code reference of
  the candidate may point one past its own truncated section (an IP-to-state entry at the cut). Limitation: a candidate cut exactly before `int3` bytes that are part of
  the target funclet's code, or before an unknown function placed without padding, is not told
  apart; the first passes wrongly (no such funclet seen), the second fails closed.
- No target `.pdata` entry outside the compared code may belong to the function: a chained
  entry whose chain reaches, directly or through other chained entries, an unwind info compared
  here is `unwind-chain-outside` (a candidate cut at a chained-entry boundary), and an entry
  whose `__CxxFrameHandler3`/`__GSHandlerCheck_EH` data names a `FuncInfo` compared here is
  `eh-funclet-outside`. The whole exception directory is scanned for this. A map entry starting
  exactly at the function's end is an adjacent function, not an overlap.
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

From 0.5.0 it also has `symbol_map_sha256`, the SHA-256 of the symbol map file exactly as the
comparator read it (absent only when a caller passes an already parsed map, which the command line
never does), and `coverage.funclet_ranges`, the `[target RVA, length]` of every compared funclet
in comparison order: addresses and lengths only, no bytes. The match gate requires every run's
map hash to equal the record's pin, and uses the funclet ranges to carry a record across map
additions that lie outside them (`docs/verification.md`, "Symbol map").

`candidate.code_section_sha256` (`code-section-sha256-v1`) identifies the compared code
independently of the object file around it, so it is identical across clean compiles of the same
source and recipe, unlike `object_sha256`. It is SHA-256 over a fixed prefix, the number of
sections, then per section in order: name length and section length, name, section bytes, the
relocation count, and each relocation sorted by offset as offset, type and the target symbol's
**name** (never its symbol-table index). When several symbols of the object share the target's
name (section symbols such as `.rdata`, repeated statics), the name does not say which is meant,
so the symbol's offset, its section's length and the SHA-256 of that section's bytes follow the
name; this adds nothing for unique names, so values computed before this rule (comparator
0.2.0) are unchanged for objects without such references. The sections are the function section first, then the
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

- `ADDR64`, `ADDR32`, `SECTION`, `SECREL7`, `TOKEN`, `SREL32`, `PAIR`, `SSPAN32` and
  `ABSOLUTE` relocations, and `SECREL` anywhere but against a thread-local variable in code. `ADDR64` in particular would also need the image's base relocations to be
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

## Versions and earlier results

| comparator | contract | change |
|---|---|---|
| 0.4.0 | 2 | EH data, funclets, chained unwind, jump tables |
| 0.5.0 | 2 | thread-local variables: `SECREL` in code against thread-local map entries, `_tls_index` from the TLS directory, the `thread-local` map entry kind; reports add `symbol_map_sha256` and `coverage.funclet_ranges` |

0.5.0 widens what can pass and also turns some 0.4.0 passes into fails. A candidate without a
`SECREL` relocation, compared with a map whose entries carry no `kind` key and which has no
`_tls_index` entry, takes exactly the 0.4.0 path, so every 0.4.0 `pass` and every 0.4.0 `fail`
other than `unsupported-relocation` for `SECREL` (and `invalid-symbol-map` for an entry without
`rva`) is the result 0.5.0 gives. Outside that set results can change in both directions: an
RVA entry with an extra `kind` key (0.4.0 ignored it) is now `invalid-symbol-map`; a `_tls_index`
entry in an image without a TLS directory, or one disagreeing with the directory, now fails
(`tls-directory-missing`, `malformed-tls-directory` or `tls-index-mismatch`); and an undefined
`_tls_index` used to resolve through the map and now resolves through the TLS directory. No
accepted function's map names `_tls_index` or gives an entry a `kind` (the repository symbol map
has neither), so no accepted result depends on these changes. The reason codes of 0.4.0 and
`candidate.code_section_sha256` are unchanged; `relocations_by_type` may now count `SECREL`, and
reports gain the two fields described under "Report".

That is a statement about results, not about records. The match gate binds every report to the
current comparator version and source hash (`docs/verification.md`, "Comparator"), so a version
change still makes every match record stale until it is regenerated by real runs, as was done
for 0.4.0. Reviewer records bind the unit digest and the code-section hash, neither of which a
comparator change alters, so regenerated records with the same digest keep their approvals and
need no re-review, full or delta.

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
