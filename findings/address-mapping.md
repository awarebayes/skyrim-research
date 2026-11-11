# Finding: Address Library mapping for the pinned target, checked against the image

Status: OBSERVED (database parse, structural and identity checks); HYPOTHESIS (carry-over of
CommonLibSSE-NG function ids beyond the checked anchors)
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), run locally; no game file,
database or game-derived output was uploaded to any service
Date (UTC): 2026-11-11
Target build id / image SHA-256: `sse-steam-1-7-104` /
`846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f` (re-measured before use; equal)
Function RVA / size (if applicable): not applicable; anchor and candidate RVAs below
Source exposure: mixed (binary-analysis of the pinned image; community-headers; a community
address database)
Sources and immutable revisions / licenses:
- Address Library for SKSE Plugins, "All in One (1.7.104.0)" v13, Nexus Mods mod 32444, downloaded
  by the maintainer. Archive SHA-256
  `be0c7c07fb63fd1c1403690d4797c7a8fdf8799118acceb605f285d7b0ee055f` (6,640,552 bytes, 24 database
  files). Database used: `versionlib-1-7-104-0.bin`, 2,263,132 bytes, SHA-256
  `8aab3dd251d135b849bd983f86a4a205c920fa3e81f8e30c0e63ccfef9423842`. For cross-version comparison
  only: `versionlib-1-6-1179-0.bin` (SHA-256
  `3ee46b2f3a8a24b9cda1f2aa63b0f0f47dea347e52701a6739327e5ea1b5838e`). Licence: Nexus file
  permissions, no open-source licence; summary below. The database is kept under `.local/` and is
  not published.
- CharmedBaryon/CommonLibSSE-NG at `b93280e832f263dbef44e44cbe2936622a02f91a`, MIT: AE ids and names
  from `include/RE/Offsets*.h` and `RELOCATION_ID` uses in `include/` and `src/`; the format-2
  reader in `include/REL/ID.h` was consulted for the 1.6.x file layout.
- Ghidra 12.2 project from `findings/ghidra-import.md` (same pins), reused without re-import.
- Not used: powerof3/CommonLibSSE (GPL-3.0, maintainer decision pending), meh321/AddressLibraryDatabase
  (no licence), SKSE64 source offsets.
Name provenance: COMMUNITY (CommonLibSSE-NG b93280e names joined through the database) checked
against EXE_RTTI where stated; no GUESS names are introduced
Confidence: high for vtable/type-descriptor ids; medium for the function anchors listed; low for
unchecked function ids

## Question and method

1. Does the archive contain a database for exactly 1.7.104.0, and what does it map?
2. Do the mapped offsets land on objects of a plausible kind in the pinned image?
3. Do CommonLibSSE-NG's AE ids (written for 1.6.x) name the same objects on 1.7.104?

Method. All scripts are original stdlib Python or Ghidra Java under `.local/`. The archive was
extracted into an empty private directory; nothing from it was executed, and Python ran with `-I`.

- Reader. NG b93280e reads only formats 1 and 2. The 1.7.x files carry format number 5, which
  that reader rejects. Their layout was inferred from the files themselves: a 0x60-byte header
  (format, four version fields, a 64-byte NUL-padded module name, pointer size, a zero field, a
  count), followed by `count` little-endian u32 offsets indexed by id, with 0 meaning unmapped. The
  reader refuses any file whose size is not exactly `0x60 + 4 * count`. Both 1.7.x files satisfy
  this. The 1.6.x files were decoded with an original implementation of the format-2 delta
  encoding as NG documents it. Every byte of each file was consumed.
- Structure. Every mapped offset was classified against the PE section table, the exception
  directory (`.pdata`) and a private export from the Ghidra project: function entries, RTTI
  `vftable` symbols with their Complete Object Locator offsets, and type descriptors.
- Identity. Each NG AE id was resolved through the database and compared with independent
  evidence in the image: the RTTI class name Ghidra derived from the EXE, vtable slot ownership,
  referenced string literals (read locally, not reproduced), and cross-references to mapped globals.
- Names were applied to the Ghidra project as non-primary labels in namespace `NG_b93280e`. Each
  label has a pre-comment giving the source file and line, whether the name is a declared
  identifier or the heuristic "nearest enclosing definition", and the check outcome.

## Permissions of the database (as copied by the maintainer)

The Nexus permission text says: uploading the file to other sites is allowed with credit;
modifying the files needs the author's permission; conversion to other games is allowed with
credit; assets may be used without permission or credit, but not in paid mods. It says nothing
about publishing values derived from the database, such as id-to-offset pairs.

Local use for analysis is not restricted by this text. Whether derived pairs count as "assets"
is unclear. **This finding therefore publishes no id/offset pairs and no database content:**
only counts, hashes, and RVAs with names from the MIT-licensed NG source. Maintainer question:
may id/offset pairs or a symbol map derived from them be published?

## Observations

Database: format 5, embedded version **1.7.104.0**, module name `SkyrimSE.exe`, pointer size 8.
565,759 id slots, 435,162 non-zero (ids 1 to 565,758). Offsets range from 0x1022 to 0x3804830,
and all 435,162 offsets are distinct.

Where the mapped offsets land (counts):

| class | count |
|---|---|
| main `.text`, Ghidra function entry and `.pdata` begin | 93,686 |
| main `.text`, Ghidra function entry, no `.pdata` begin (leaf or untracked) | 74,572 |
| main `.text`, `.pdata` begin, no Ghidra function | 84 |
| main `.text`, strictly inside a `.pdata` range | 1 |
| main `.text`, none of the above | 17,338 |
| `.rdata`, RTTI vftable start | 8,637 |
| `.data`, RTTI type descriptor | 8,136 |
| `.rdata`, other | 182,786 |
| `.data`, other | 49,663 |
| second `.text` (non-executable) | 259 |
| `.bind`, `.pdata`, `.rsrc`, `.reloc`, outside any section | 0 |

Reverse coverage: 168,258 of the 175,998 Ghidra functions in the main `.text` are mapped, as are
93,770 of 122,258 `.pdata` begins in code. Every RTTI vftable (8,637 of 8,637) and every type
descriptor (8,136 of 8,136) is a mapped offset. The 17,338 code offsets that are neither a function
entry nor a `.pdata` begin were not examined individually.

Cross-version (1.6.1179.0 to 1.7.104.0): 390,395 ids appear in both databases. 38,115 appear
only in 1.6.1179; 44,767 appear only in 1.7.104, and 42,624 of those are above 1.6.1179's highest
id. Sorted by 1.6.1179 offset, 388,561 of 390,394 adjacent pairs keep their order in 1.7.104. The
offset change is piecewise constant (9,346 runs).

NG coverage: NG b93280e yields 18,220 id rows and 17,730 distinct AE ids (rows: 8,814 vtable
entries, 8,273 RTTI, 410 NiRTTI, 203 `Offsets.h` entries, 520 from function bodies). 16,447 of them are in the 1.7.104
database; 16,444 are in 1.6.1179. Of the NG ids missing from 1.7.104, all but 4 are also missing from
1.6.1179. The 4 exceptions are 2 vtable ids and 2 function ids. 16,460 labels were applied (0
failures).

Identity checks:

| check | evidence independent of the database | result |
|---|---|---|
| NG `VTABLE_<X>[k]` id lands on the RTTI vftable of class X | class name from the EXE's RTTI | 8,013 of 8,015 mapped agree (6,707 exact, 1,306 after normalizing spelling of templates, `__ptr64`, anonymous namespaces); of 6,775 mapped `[0]` entries 6,774 are primary (COL offset 0); **2 fail** |
| NG `RTTI_<X>` id lands on the type descriptor named X | EXE RTTI | 7,319 of 7,321 agree; **2 fail** |
| NG `NiRTTI_<X>` | name pointer in the file | 410 not checkable: the name pointer is zero in the file (set at run time) |
| NG function ids land on a Ghidra function entry | Ghidra analysis | function-body ids used as `func_t`: 433 of 434 mapped (1 lands in `.rdata`, unexplained). `Offsets.h` entries: 157 on function entries, 42 in `.data`/`.rdata`, all with data-like names (`Singleton`, `Vtbl`, ...) |
| NG function name is a virtual of its class | vtable slot ownership from RTTI | 19 land in a slot of the named class. 3 land in another class's slot: 2 belong to the header's real class (my heuristic named the wrong class), and 1 is unexplained |
| function references a string naming its own operation | string literals referenced in the body | 22 NG-named functions reference strings; all 22 read as consistent; 7 contain the method's own words |
| NG singleton/global is referenced by NG functions of the same class | cross-references | of 123 data names (122 RVAs), 12 are referenced by a same-class NG function, 50 by other NG functions, 61 only by unnamed functions; none unreferenced |

Individual anchors (build `sse-steam-1-7-104`; names COMMUNITY from NG b93280e; the RTTI
comparison is EXE_RTTI):

| # | kind | RVA | community name | independent evidence | result |
|---|---|---|---|---|---|
| 1 | vtable | 0x181a620 | `VTABLE_TESObjectWEAP[0]` | RTTI vftable of TESObjectWEAP, COL 0; equals the primary vftable in `findings/ghidra-import.md` | identity supported |
| 2 | vtable | 0x185ec20 | `VTABLE_TESNPC[0]` | same, TESNPC | identity supported |
| 3 | vtable | 0x18f5b98 | `VTABLE_ActiveEffect[0]` | same, ActiveEffect | identity supported |
| 4 | vtable | 0x196d980 | `VTABLE_PlayerCamera[0]` | same, PlayerCamera | identity supported |
| 5 | vtable | 0x18ebbe0 | `VTABLE_TESCamera[0]` | same, TESCamera | identity supported (size anchor still unsupported) |
| 6 | function | 0x6227f0 | `Offset::BGSSaveLoadManager::Save` | references a refusal-to-save message; references the UI and SkyrimVM singletons | identity supported |
| 7 | function | 0x90b9d0 | `Offset::Console::SetSelectedRef` | references a console selection string and a selection format string | identity supported |
| 8 | function | 0x280290 | `TESObjectBOOK::Read` | references spell-learned UI strings | identity supported |
| 9 | function | 0x2f2840 | `TESObjectREFR::Enable` | references an "enable"-related diagnostic string | identity supported |
| 10 | function | 0x14a9c10 | `Offset::BSScript::NF_util::NativeFunctionBase::Call` | references native-call failure strings | identity supported |
| 11 | function | 0x73ad90 | `ArmorRatingVisitor::HaveNotVisitedArmor` | slot of ArmorRatingVisitor's RTTI vftable | kind and class supported |
| 12 | function | 0x7499e0 | `PlayerCharacter::AddSkillExperience` | slot of PlayerCharacter's RTTI vftable | kind and class supported |
| 13 | global | 0x3230778 | `Offset::PlayerCharacter::Singleton` | in `.data`; referenced from 1,264 functions including NG-named PlayerCharacter methods | consistent |
| 14 | global | 0x31a5698 | `Offset::PlayerControls::Singleton` | referenced by NG's `PlayerControls::Ctor` | consistent |
| 15 | vtable | 0x1ac4ca0, 0x1ac4ce0 | `VTABLE_AutoRegisterCreator_MovementMessageFreezeDirection_...[0]`, `VTABLE_BSTDerivedCreator_MovementMessageFreezeDirection_...[0]` | each id lands on the other class's vftable | **fail**: the pair is swapped on this build |
| 16 | RTTI | 2 type descriptors in `.data` | two `RTTI_BSPlatform__BSAsyncRequest_std__function_...` | descriptors exist but their template arguments differ from NG's names | **fail** |
| 17 | function | 0xba4300 | `BoneNodeEntry::SetGraphVariableBool` (heuristic name) | lands in an hkpTriggerVolume vftable slot | **unexplained** |

## Interpretation and alternatives

**The anchors support the Address Library mapping on this build for data objects with RTTI, and
for the specific functions listed.** The vtable and type-descriptor checks are the strongest
evidence. Ghidra derives class names from the EXE's own RTTI, independently of the database. NG's
AE ids, written against 1.6.x, still name the same RTTI object on 1.7.104 in 15,332 of 15,336
mapped cases. That holds only because the database's 1.7.104 table preserves the AE id space. The
cross-version order preservation and the high-id-only additions agree with this.

What does not carry over, or is not shown:

- Function ids. Only the ~20 function anchors with string, vtable-slot or cross-reference evidence
  have support beyond "lands on a function entry". Landing on an entry is a kind check, not an
  identity check: 168,258 of 175,998 entries are mapped, so almost any id lands on some function.
- 2 swapped vtable ids and 2 renamed RTTI types show that individual ids can be wrong or reassigned
  on 1.7.104. Each new use needs its own check.
- 4 NG ids present in 1.6.1179 are absent from 1.7.104, and roughly 1,280 NG ids are in neither
  database. Ids above 522,614, new in 1.7.x, have no NG names.
- Nothing here checks signatures, field offsets or behaviour. NG layouts remain 1.6.x declarations
  (see the size anchors in `findings/ghidra-import.md`).
- 520 function-body names come from a "nearest enclosing definition" heuristic. It mislabeled at
  least 3 cases (a nested class, a header class, and one id with two names). Ghidra labels mark these
  as heuristic.

Alternative explanations: string consistency was judged by reading, so a function that merely
calls the real one could also match. The unexplained hkpTriggerVolume slot may be identical-code
folding, or the heuristic name may be wrong; it was not investigated.

## Pilot candidates for plan step 5 (not inventory entries)

Selection: NG-named functions whose single `.pdata` entry covers exactly the Ghidra body. Each has
UNWIND_INFO version 1 with no handler or chain flags, which the comparator's v1 unwind scope
supports. Each is under 100 bytes, a single contiguous range, not a thunk and not middleware.
Whether any of them came from one of the 68 LTCG objects is unknown; it cannot be told per function
from the measurements here. Names were confirmed by reading the cited NG line. The cross-version
column shows that each id exists in 1.6.1179 and moved by the same delta as its 6 nearest neighbours.
That is continuity, not identity.

| build id | RVA | size | community name (NG b93280e source) | calls | data refs | unwind codes | identity evidence |
|---|---|---|---|---|---|---|---|
| sse-steam-1-7-104 | 0x73ad90 | 84 | `ArmorRatingVisitor::HaveNotVisitedArmor` (`src/RE/A/ArmorRatingVisitor.cpp`) | 0 | 4 | 4 | vtable slot of named class |
| sse-steam-1-7-104 | 0x7499e0 | 47 | `PlayerCharacter::AddSkillExperience` (`src/RE/P/PlayerCharacter.cpp`) | 1 | 4 | 1 | vtable slot of named class |
| sse-steam-1-7-104 | 0x1cdc10 | 47 | `Offset::TESFile::GetCurrentSubRecordType` (`include/RE/Offsets.h`) | 1 | 0 | 2 | declared id only; 386 references |
| sse-steam-1-7-104 | 0x1ca460 | 36 | `TESFile::OpenTES` (`src/RE/T/TESFile.cpp`) | 1 | 1 | 1 | id only |
| sse-steam-1-7-104 | 0x3b4f90 | 38 | `TESFaction::SetFactionFightReaction` (`src/RE/T/TESFaction.cpp`) | 1 | 0 | 2 | id only |
| sse-steam-1-7-104 | 0x6dc5d0 | 43 | `ActorEquipManager::EquipShout` (`src/RE/A/ActorEquipManager.cpp`) | 1 | 3 | 1 | id only |
| sse-steam-1-7-104 | 0x2e6f30 | 68 | `TESObjectREFR::GetScale` (`src/RE/T/TESObjectREFR.cpp`) | 1 | 3 | 3 | id only; 73 references |
| sse-steam-1-7-104 | 0x24cda0 | 37 | `ScreenSplatter::Clear` (`include/RE/S/ScreenSplatter.h`) | 1 | 0 | 2 | id only |
| sse-steam-1-7-104 | 0x240f50 | 54 | `BSPointerHandleManagerInterface::GetHandle` (`include/RE/B/BSPointerHandle.h`) | 1 | 1 | 2 | id only; template in NG |
| sse-steam-1-7-104 | 0xceea80 | 27 | `Rumble::DisableRumble` (`src/RE/R/Rumble.cpp`) | 1 | 2 | 1 | id only; NG says it wraps an import, which the comparator v1 cannot follow through a thunk |

"Calls" and "data refs" are Ghidra reference counts. A call target, or an `ADDR64`/import
reference, may still put a candidate outside the comparator's v1 scope, which only a build will
show. No bytes, disassembly or reconstructed source are recorded.

## Reproduction and sanitized evidence

From the repository root, with private paths as placeholders:

```sh
mkdir .local/inputs/address-library/extracted          # must be new and empty
unzip -q '/path/to/Address Library All in One (1.7.104.0) v13 ....zip' -d .local/inputs/address-library/extracted
E=.local/experiments/address-mapping; P=.local/inputs/address-library/extracted/SKSE/Plugins
python3 -I $E/addrlib.py $P/versionlib-1-7-104-0.bin $P/versionlib-1-6-1179-0.bin
python3 -I $E/ng_ids.py /path/to/CommonLibSSE-NG@b93280e $E/ng_ids.tsv
# Ghidra 12.2 headless, read-only, over the project from findings/ghidra-import.md:
#   -postScript ExportImage.java $E/image-export.txt
python3 -I $E/classify.py /path/to/SkyrimSE.exe $P/versionlib-1-7-104-0.bin $E/image-export.txt $P/versionlib-1-6-1179-0.bin
python3 -I $E/anchors.py /path/to/SkyrimSE.exe $P/versionlib-1-7-104-0.bin $E/image-export.txt $E/ng_ids.tsv $E/anchor-details.tsv
#   -postScript RefSurvey.java $E/refsurvey-in.txt $E/refsurvey-out.txt   (read-only)
#   -postScript ApplyLabels.java $E/labels.tsv $E/apply-labels.log        (writes labels)
python3 -I $E/candidates.py /path/to/SkyrimSE.exe $E/anchor-details.tsv $E/refsurvey-out.txt $E/candidates.tsv
```

The exact sequence is in the private handoff. Private evidence: `.local/experiments/address-mapping/`
(summaries, anchor details, string survey, labels) and the labelled project under `.local/analysis/`.

## Negative results and limitations

- 4 identity failures (anchors 15 and 16) and 1 unexplained slot (anchor 17).
- NiRTTI ids (410) could not be checked statically.
- The format-5 layout is inferred from two files and an exact-size check, not from a published
  specification.
- 17,338 code offsets that are neither a function entry nor a `.pdata` begin, and 232,449
  `.rdata`/`.data` offsets that are not RTTI objects, were not examined. They are counts, not
  checks.
- Only CommonLibSSE-NG b93280e names were used. GPL and unlicensed sources were not consulted.
- One run on one host; not reproduced by a second person.

## Reviewer and outcome

Pending maintainer review. Open question for the maintainer: publication of id/offset pairs under
the Nexus permissions.
