# Finding: first pilot function selected, reconstructed and re-checked

Status: **comparator pass reproduced on 3 hosts (2 compiling, 3 comparing); awaiting maintainer
review; not accepted.** The inventory entry stays `mapped`. Range, unwind form and reference
counts are OBSERVED on the pinned image. The reconstructed source is not published here.
Author / human operator: awarebayes
AI assistance / model: Claude Code workers. Engineer (claude-opus-5-5): task p3-first-function-prep
(selection and analysis, local) and task p3-second-host-and-gate (re-check). Drafter
(claude-sonnet-5-5): task p3-first-function-draft (reconstruction). With the recorded G5 grant, only
`SkyrimSE.exe` and the reconstructed source were uploaded, to private Boat machines, and deleted
afterwards. The Address Library database and Ghidra material stayed on the Mac.
Date (UTC): 2026-11-11
Target build id / image SHA-256: `sse-steam-1-7-104` /
`846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f` (re-measured before use; equal)
Function RVA / size (if applicable): RVA `0x73ad90`, size 84 bytes (range `[0x73ad90, 0x73ade4)`)
Source exposure: mixed (binary-analysis of the pinned image, including a local instruction listing
and decompiler output read by the worker model named above; community-headers; a community
address database)
Sources and immutable revisions / licenses:
- CharmedBaryon/CommonLibSSE-NG `b93280e832f263dbef44e44cbe2936622a02f91a`, MIT:
  `src/RE/A/ArmorRatingVisitor.cpp`, `include/RE/A/ArmorRatingVisitor.h`,
  `include/RE/A/ArmorRatingVisitorBase.h`, `include/RE/B/BSTArray.h` (name, signature, member layout).
- Address Library for SKSE Plugins "All in One (1.7.104.0)" v13 (Nexus mod 32444),
  `versionlib-1-7-104-0.bin` SHA-256 `8aab3dd251d135b849bd983f86a4a205c920fa3e81f8e30c0e63ccfef9423842`;
  AE id 40297 resolves to RVA `0x73ad90`. See `findings/address-mapping.md` for permissions.
- Ghidra 12.2 project from `findings/ghidra-import.md` (opened read-only; not re-imported).
- powerof3/CommonLibSSE (GPL-3.0): not consulted; NG was sufficient for this function.
Name provenance: COMMUNITY (`ArmorRatingVisitor::HaveNotVisitedArmor`, CommonLibSSE-NG b93280e),
not verified; class identity supported by EXE_RTTI (see below)
Confidence: high for the measured properties; medium for the community name; unknown for the
compiler group and LTCG membership

## Question and method

Plan step 5, first three boxes (issue #6, work item `first-function`): select one short function
that contract v1 of the comparator (`docs/comparator-contract.md`) can check completely, add it to
the inventory as `mapped`, and analyze it locally so that a reconstruction loop can start.

1. Checked the image SHA-256 against `builds/target.json`.
2. Re-measured each candidate from `findings/address-mapping.md` directly from the image with an
   original stdlib script over `tools/pecoff.py`: every `.pdata` entry that intersects the range,
   its `UNWIND_INFO` header, and every DIR64 base relocation inside the range (an `ADDR64`
   reference would put a function outside contract v1).
3. Listed each candidate's instructions and references, and its decompiler output, with an original
   read-only Ghidra script. The output stays under `.local/`.
4. Resolved the AE id through the Address Library database and compared it with the RTTI
   vftable slot and with NG's declarations.
5. Built private comparator inputs (task, recipes, symbol map) and a wrapper,
   `tools/verifier/verify_function.py`, then ran negative cases against the real image.

## Observations

Selected function, build `sse-steam-1-7-104`:

| property | value |
|---|---|
| RVA / size | `0x73ad90` / 84 bytes, main `.text` |
| `.pdata` entries intersecting the range | exactly 1, begin and end equal to the range |
| unwind form | `UNWIND_INFO` version 1, no handler, not chained, no frame register; 4 code slots (two non-volatile register saves, no stack allocation) |
| calls / RIP-relative data references / imports | 0 / 0 / 0 |
| DIR64 base relocations in range (`ADDR64`) | 0 |
| bytes the comparator will compare | 84 exact, 0 by reference; plus 12 bytes of unwind info |
| references to the entry | 2: its `.pdata` entry, and slot 4 of the RTTI vftable of `ArmorRatingVisitor` |

The earlier candidate table listed "4 data refs" for this function. Those were stack-slot operands
counted by Ghidra's reference survey, not relocatable references. The measured count is 0.

Name and identity:

- AE id 40297 lands on this entry. NG uses that id inside `ArmorRatingVisitor::HaveNotVisitedArmor`
  itself, so the name is not a heuristic for this id.
- Independent check (EXE_RTTI): the entry is slot 4 of the vftable whose RTTI type is
  `ArmorRatingVisitor`, and NG declares `HaveNotVisitedArmor` as virtual slot 04 of that class.
  This supports the class and slot. It does not prove the method name, which is NG's.
- EXE_RTTI also shows the class lives in an anonymous namespace (the type descriptor name has an
  `_anon_` prefix) together with `ArmorRatingVisitorBase` and `GetClothingValueVisitor`. That puts
  the three classes in one translation unit. A reconstruction must still use a named namespace,
  because contract v1 needs an external symbol.
- The function reads two members of the class. Their offsets agree with NG's declared layout of
  `ArmorRatingVisitor::armors` (`BSScrapArray<TESObjectARMO*>`). This supports those two offsets on
  this build. It does not support the rest of NG's layout.

Compiler group (plan step 5 asks to record origin uncertainty):

- The compiler group is not observable per function. The Rich header gives object counts per
  toolset build, not per function, so membership in the 27054 group cannot be shown.
- Indications, all inference: the function and its neighbours are methods of the same
  anonymous-namespace classes and sit next to each other. That fits one object's COMDATs laid out
  in order, and it happens with or without LTCG. No local evidence for or against LTCG was found.
  As a virtual function with the standard x64 convention, it would look the same either way.
  Game code is more likely than middleware: NG names it, the class is game-specific, and its
  vftable sits among game classes. A first-attempt mismatch may therefore reflect the compiler
  group or LTCG, not only the source.

Rejected candidates: none. The first candidate met every contract v1 condition, so the others in
`findings/address-mapping.md` were not needed. Two backups of a different shape (one with a single
direct call, one with a call and a RIP-relative data read) were measured the same way. Each has
exactly one `.pdata` entry equal to its range, simple version-1 unwind info and no `ADDR64`. They
are recorded privately and are not inventory entries.

## Verifier preparation

`tools/verifier/verify_function.py` (new, data-free) reads a task description file (the contract
task plus paths to the recipe and symbol map) and is given a candidate object, its build record,
the target image and a report path. It runs `tools/compare.py` unchanged and writes the
comparator's sanitized report. Byte-level diagnostics go only under `.local/`. It prints a short
summary: result, reason code, the comparator's sanitized detail, a one-line hint per reason code,
coverage counts and the private diagnostics path. The summary never prints bytes. It refuses to
summarize a report that lacks `acceptance: not-evaluated` or holds a long hex run. Unit tests:
`tests/test_verify_function.py`, synthetic fixtures only.

Negative cases on the real pinned image, run on the Mac without any Microsoft compiler. The
candidate objects were made with `tests/synthetic_pecoff.py` and carry the task's symbol name:

| case | expected | result / reason |
|---|---|---|
| synthetic code of the right length (84 bytes) | rejected | fail / `code-byte-mismatch` at +0x0 |
| a different image (synthetic PE) given as target | rejected | fail / `image-hash-mismatch` |
| task pins a hash other than the manifest's | rejected | fail / `manifest-mismatch` |
| candidate shorter than the range (80 of 84 bytes) | rejected | fail / `function-size-mismatch` |
| task range truncated to 80 bytes, candidate = the target's own first 80 bytes, map has the true size | rejected | fail / `symbol-map-conflict` |
| same, with the task symbol removed from the map | rejected | fail / `unwind-entry-crosses-boundary` (all 80 compared bytes agreed) |
| object not the one named by its build record | rejected | fail / `object-provenance-mismatch` |

The last truncation case shows that a range cut short inside a real function fails even when every
compared byte agrees. Its object held target code, so it was deleted after the run; only its hash
is kept privately. **No positive case was produced or attempted.** No report claims a match.

## Reconstruction and second-host re-check

The Drafter's first reconstruction compiled to a passing comparison on the standing Boat verifier
machine. It was compiled twice there, and both runs passed. An independent re-check then did the
following:

1. **Inputs.** The source, recipe, both objects and the image were re-hashed on the Mac and equal
   the build records and reports. The task's RVA and size equal the inventory and the image's
   single `.pdata` entry. With no relocations, the symbol map matters only for placement checks.
   The reports hash the same image bytes they compare.
2. **Independent parser.** A separate stdlib COFF/PE reader that does not use `tools/pecoff.py`
   extracted the function's COMDAT section and its `.pdata`/`.xdata` from each object. All 84
   code bytes and the 12 unwind bytes equal the image's.
3. **Integration.** The source was split into one translation unit, a class header plus a .cpp
   (proposed layout `reconstruction/inventory/ArmorRatingVisitor.{h,cpp}`). Only comments and
   NG's member names changed; no code changed. Its revision is the digest of both files (`tu-sha256-v1`,
   `615045612a209905c4d4f49ef35574b4bddb4a6b76a4c2cf69691b531517f85f`).
4. **Hosts.** Same recipe (`recipe_sha256` `923a7ef7ea6d9792a66669014f059f40af29e111b065f2ae6b0a6835d7f4e838`),
   cl 19.16.27054 x64 under Wine, comparator 0.1.0
   (source hash `da2180f0a93f3e1c9c19ea7164f5c7e7db968b872756023973630726cacb86e5`):

| host | how it got the compiler | compiled | compared | integrated source | Drafter's source |
|---|---|---|---|---|---|
| standing verifier machine (Drafter's runs) | pinned recipe, pilot | yes | yes | not run | pass, twice |
| fork of the stopped standing machine | copy of the standing disk | yes | yes | pass | pass |
| fresh machine built by `setup_boat_machine.sh` | pinned recipe, from scratch; binaries matched `pinned.sha256` | yes | yes | pass | pass |
| macOS arm64 (operator's Mac) | none | no | objects from both Boat hosts | pass, both | pass (fork object) |

Independence: the fork is a second machine but not a second environment. It shares the standing
machine's disk, toolchain install and Wine. The fresh machine installed the toolchain again from
the pinned manifest. Its compiler binaries hash the same, and it uses the same Ubuntu image and
Wine package, so it is independent of the standing install but not of the recipe. The Mac run checks the
comparator on a different OS and CPU architecture over the same objects; it does not compile.

Negative cases on both Boat hosts, same result on each (`reports/sse-steam-1-7-104/0x73ad90-recheck-cases.json`):

| case | result / reason |
|---|---|
| integrated source with the return condition inverted | fail / `code-byte-mismatch` at +0x4c |
| correct object, task moved to the preceding function (0x73ad00, 95 bytes), map unchanged | fail / `symbol-map-conflict` |
| same range, map edited to place the task symbol there | fail / `function-size-mismatch` (84 vs 95) |
| correct object, task at the following function's start (0x73ae00, 84 bytes), map edited | fail / `code-byte-mismatch` at +0x7 |

Whole-object hashes differ between clean compiles. A field-level comparison of four objects
(two by the Drafter, one per new host) found differences only in these places. The COFF header
`TimeDateStamp` differs. The `S_OBJNAME` record in `.debug$S` holds the absolute object path
(Wine `Z:\...` form), so its length moves every later `PointerToRawData`/`PointerToRelocations`
and `PointerToSymbolTable` by the length difference. The `.debug$S` symbol's auxiliary length
changes with it. The `.chks64` entry for `.debug$S` differs too. The other 16 of the 18 sections have
identical contents and relocations, including the function's COMDAT and its unwind data. The two new hosts' objects are the same
size (3614 bytes); only the timestamp, the path and that checksum differ. The build record
therefore binds each run to its own object, which is what the comparator contract requires.
Reproduction is every run passing from the same source digest, recipe and image, not identical
objects. Neither `docs/verification.md` nor the contract requires identical objects, so nothing
was loosened. Pinning a normalized object hash as well would need a reviewed contract change. A
fixed build directory plus a timestamp-free compiler option might make whole objects identical;
that is untested here and would be a new recipe.

The reports name the comparator version as `comparator.version` (`0.1.0`) beside
`comparator.source_sha256`, as the contract lists. No report field is named `comparator_version`,
so a reader looking for that top-level key finds nothing. That is not a reporting bug.

## Interpretation and alternatives

This function is a good first target for contract v1. Every byte is compared exactly, and there are
no relocations, so a wrong symbol map cannot affect the result. Unwind info is compared in full.
A mismatch will therefore point at the source, the compiler or the flags, not at the comparator's
reference handling. The cost is that it exercises none of the relocation paths. The backups, which
carry `REL32` call and data references, cover those next.

Alternatives to the community name: NG could have the slot right and the method name wrong. A
byte match would not settle the name (`docs/plan.md` step 5).

## Reproduction and sanitized evidence

From the repository root, with private paths as placeholders:

```sh
shasum -a 256 /path/to/SkyrimSE.exe        # must equal image_sha256 in builds/target.json
python3 -I .local/experiments/first-function/inspect.py /path/to/SkyrimSE.exe <private-out> 0x73ad90:84
# Ghidra 12.2 headless, read-only, project from findings/ghidra-import.md:
#   -postScript FunctionDump.java <private-out>/dump.txt 73ad90
python3 -I .local/tasks/first-function/make_inputs.py /path/to/SkyrimSE.exe
python3 -I .local/experiments/first-function/negatives.py /path/to/SkyrimSE.exe
python3 -m unittest tests.test_verify_function -v
```

The re-check's reproduction command is in `reports/sse-steam-1-7-104/0x73ad90.json`
(`reproduction`). It needs the reconstructed source, which is not published here.

The private notes, listings, task inputs and negative-case reports are under `.local/`. Nothing
here contains code bytes, disassembly, decompiler output or reconstructed source.

## Negative results and limitations

- A byte match shows that this source and recipe produce the checked code. It does not verify
  the community method name, which is NG's, and it does not show the original source looked
  like this. Only the class, the vftable slot and two member offsets were checked otherwise.
- The compiler group and LTCG membership are unknown. The match shows this compiler and these
  flags can produce these bytes; it does not show the game was built with them.
- Host independence is partial (see the table): the fork shares the standing install, all Boat
  hosts share the recipe, Ubuntu image and Wine package, and the Mac only compares.
- The function has no relocations. The match exercises none of the comparator's reference paths.
- The symbol map (`reports/sse-steam-1-7-104/symbol-map.json`, Address Library id/offset pairs)
  covers the function and two neighbours only. It is not a general map.
- Not accepted. Publishing the reconstructed source, and the gate change that would allow
  `matched`, wait on maintainer review.

## Reviewer and outcome

Pending maintainer review: provenance and publication of the reconstructed source, an
independent re-run of the comparison, and the proposed gate change. Status: `mapped`; comparator
pass reproduced, not accepted.
