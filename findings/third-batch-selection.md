# Finding: third batch of 40 functions in eight class units, selected by a scripted plan

Status: OBSERVED properties of the pinned image; selection only. Nothing reconstructed or compared.
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), task p5-batch-prep; local only
Date (UTC): 2026-11-12
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): see the table
Source exposure: mixed (binary-analysis of the pinned image in local Ghidra 12.2; community-headers; a community address database)
Sources and immutable revisions / licenses: CharmedBaryon/CommonLibSSE-NG `b93280e832f263dbef44e44cbe2936622a02f91a` (MIT) for every published name;
Address Library 1.7.104.0 `versionlib-1-7-104-0.bin` SHA-256 `8aab3dd251d135b849bd983f86a4a205c920fa3e81f8e30c0e63ccfef9423842`
(publishing id/offset pairs approved, `docs/authorizations.md`); powerof3/CommonLibSSE `654e55f7979c1733033d5dbef176e43827bac944`
(GPL-3.0) consulted locally as a naming fallback only; nothing from it is published here.
Name provenance: COMMUNITY (unverified; "decl." is the identifier NG declares for the id, "encl." the nearest enclosing NG definition, a heuristic)
Confidence: high for sizes, unwind forms and reference counts; low to medium for names

## Question and method

Does grouping functions by class, one Drafter per class, cut the cost per function? This batch is
the input for that measurement. `tools/ghidra/export_pack.py plan` reclassified the 579 functions that
NG names through the Address Library (`survey --named`) and kept a function only if: its verdict is
`supported` for comparator contract v1, or `caution` solely because it is a leaf without `.pdata`
followed by int3 padding; NG names it (not the GPL fork alone); it has an owning class whose NG body
declares the method (guards against the enclosing-name heuristic); it is not middleware or a free
function; it is at most 500 bytes; it is not already in the inventory. A class qualified with at least
4 such functions and an area under `reconstruction/README.md`. Per class the plan takes the two
smallest functions over 100 bytes where they exist, then the smallest others, within 1,200 bytes, and
picks one class per kind (form, extra data, NetImmerse, BS utility, menu/UI, magic, actor, manager),
filling missing kinds from unused kinds. `packs` then wrote per-function packs, one class-level
directory per class (vtables, offsets observed across all its selected functions, declarations) and
one task per class.

## Observations

| unit | recipe | functions / bytes | RVA (AE id) size `method` name-kind unwind references |
|---|---|---|---|
| `forms/TESObjectREFR` | msvc-19.16.27054-o2 | 6 / 650 | `0x2e6f30` (19664) 68 `GetScale` e v1/3 1C 1R 1U; `0x2e73a0` (19670) 84 `CanBeMoved` e v1/2 1C 1R 1U; `0x2e5a60` (19627) 86 `HasQuestObject` e v1/1 2C 2U; `0x2f3b70` (19812) 117 `GetCurrentLocation` e v1/2 3C 1R 2U; `0x300b90` (20205) 143 `GetCalcLevel` e v1/2 3C 5R 2W 7U; `0x2eee20` (19753) 152 `GetTransform` e v1/6 2C 1R 2U |
| `inventory/InventoryChanges` | msvc-19.16.27054-o2 | 5 / 810 | `0x22b710` (16047) 11 `GetItemCount` e leaf 2A; `0x233f90` (16072) 44 `InitOutfitItems` e v1/1 1C 1U; `0x2372c0` (16095) 58 `VisitInventory` e v1/4 -; `0x237300` (16096) 262 `VisitWornItems` e v1/10 2C 2A 4U; `0x237a20` (16099) 435 `RemoveFavorite` e v1/12 7C 6U |
| `netimmerse/NiAVObject` | msvc-19.16.27054-o2 | 4 / 127 | `0x1053280` (77998) 23 `SetCollisionLayer` e v1/1 1C 1U; `0x10532a0` (77999) 28 `SetCollisionLayerAndGroup` e v1/1 1C 1U; `0x405a50` (26022) 33 `GetCollisionObject` e v1/1 1C 1U; `0x105a360` (78103) 43 `UpdateRigidConstraints` e v1/1 2C 2U |
| `bsengine/BSReadWriteLock` | msvc-19.16.27054-o2 | 4 / 269 | `0xce3510` (68239) 5 `UnlockForRead` d leaf -; `0xce3520` (68240) 26 `UnlockForWrite` d leaf -; `0xce3250` (68233) 112 `LockForRead` d v1/4 2R 2I; `0xce32d0` (68234) 126 `LockForWrite` d v1/8 2R 2I |
| `bsengine/BSDirectInputManager` | msvc-19.16.27054-o2 | 4 / 324 | `0xcfaeb0` (68676) 37 `ReleaseDevice` e v1/2 -; `0xcfae70` (68675) 48 `CreateDeviceWithGUID` e v1/1 -; `0xcfaee0` (68677) 113 `GetDeviceState` e v1/6 1C 1U; `0xcfaf60` (68678) 126 `GetDeviceData` e v1/6 - |
| `magic/MagicCaster` | o2-fpfast | 4 / 489 | `0x5c2cc0` (34204) 57 `GetCurrentSpellCost` e v1/2 1C 1R F; `0x5caae0` (34408) 104 `InterruptCast` e v1/2 4C; `0x5cef10` (34456) 163 `FindPickTarget` e v1/8 2C 1U; `0x5cdf50` (34448) 165 `PlayReleaseSound` e v1/4 5C 1R 1U F |
| `actors/Actor` | msvc-19.16.27054-o2 | 7 / 300 | `0x6797a0` (37334) 13 `GetLevel` d leaf 1C; `0x6cb920` (38590) 14 `IsAttacking` e leaf -; `0x6d7750` (38783) 16 `HasShout` e leaf 1C 1U; `0x6af1b0` (37960) 20 `GetMoveDirectionRelativeToFacing` e leaf 1J 1U; `0x6d92b0` (38808) 20 `GetVoiceRecoveryTime` e leaf 1J 1U; `0x687c20` (37491) 102 `IsInRagdollState` e v1/2 -; `0x6c5440` (38469) 115 `GetActorValueModifier` e v1/2 1C 1U |
| `forms/TESFile` | msvc-19.16.27054-o2 | 6 / 919 | `0x1ca460` (13931) 36 `OpenTES` e v1/1 1C 1U; `0x1cdc10` (13988) 47 `GetCurrentSubRecordType` d v1/2 1C 1U; `0x1cd7d0` (13982) 72 `GetFormType` d v1/2 3C 3U; `0x1cdc60` (13990) 167 `SeekNextSubrecord` d v1/2 2C 3R 5U; `0x1ce7e0` (14018) 188 `Duplicate` d v1/4 2C 4R 2I 3U; `0x1cd860` (13984) 409 `Seek` d v1/6 5C 6R 3I 8U |

Key: name-kind `d` = NG declares the identifier for the id, `e` = nearest enclosing NG definition;
unwind `leaf` = no `.pdata` (size from analysis, int3 padding follows), `v1/n` = version 1 with n code slots;
references C call, J tail jump, R read, W write, A address, I import, U target without a community name
(any name a Drafter gives it is a GUESS), F float equality without a parity branch. `actors/Actor` extends
the unit of the accepted `0x2e7fc0`, which every attempt re-checks. In total 40 functions, 3,888 bytes.
No function in range has a DIR64 relocation, a jump table, an exception handler or more than one
`.pdata` entry.

## Interpretation and alternatives

Two kinds had no qualifying class: no `Extra*` class and no menu/UI class has 4 eligible functions
(the UI candidates are Scaleform `GFxValue::ObjectInterface`, middleware, and `UI3DSceneManager`, 3).
`InventoryChanges` (area by rule 1, as for the existing inventory visitors) and `TESFile` (a `TES`
class that is not a `TESForm` by RTTI, so not counted as a form) fill those slots. `MagicCaster` has
no prefix rule; `magic/` is proposed under rule 1 (NG's `MagicSystem` types) and needs the
maintainer's confirmation. Two of its functions test float equality without a parity branch, the
pattern behind the earlier `/fp:fast` match; its other two do no float arithmetic, compare or
conversion, so the whole unit takes `o2-fpfast` (inference: the flag does not change them). A
separate `MagicCaster_fpfast` unit was not used, because the source lint ties a unit's file name to
the class it declares. Rejected alternatives: `BSSoundHandle` (12 eligible, none over 100 B),
`NiTimeController` (8, but a second extension of an accepted unit), `PlayerCharacter` (7, a second
actor class), `TaskQueueInterface` and `TES` (8 and 5, no area rule). Classes that more than one
unit uses, the candidates for shared headers: `Actor`, `TESObjectREFR`, `TESForm`, `NiRefObject`,
`MagicTarget`, `TESObjectCELL`.

## Reproduction and sanitized evidence

`python3 tools/ghidra/export_pack.py survey --named`, then `plan --label batch3 --extend Actor --area
InventoryChanges=inventory --area MagicCaster=magic --task-prefix batch3- --total 40`, then `packs
<plan list> --attempts-per-function 4 --fpfast unit --class-material`, with a private config
(`tools/ghidra/README.md`); once these entries are in the inventory, add `--reuse-evidence
findings/third-batch-selection.md` to `plan` (checked: it then proposes the same 40). Packs, listings and decompiler output stay under `.local/`. Survey of the
579 NG-named functions: 224 supported, 60 caution, 295 unsupported; 104 classes own a supported or
caution function, 17 of them at least 4.

## Negative results and limitations

Verdicts predict the comparator; only a comparator run decides. Names come from a heuristic join and
are unverified. Leaf sizes without `.pdata` come from Ghidra. The `/fp:fast` signal is a listing
pattern, not a measurement. One host, one run.

## Reviewer and outcome

Not reviewed. Inventory entries added as `mapped` only.
