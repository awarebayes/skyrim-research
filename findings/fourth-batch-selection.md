# Finding: fourth batch of 148 functions in 20 classes, ordered by fan-in from a whole-image table

Status: OBSERVED properties of the pinned image; selection only. Nothing reconstructed or compared.
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), task p7-class-skeletons; local only
Date (UTC): 2026-11-12
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): private plan `.local/packs/_plan/fourth-batch/` (list, plan, inventory rows)
Source exposure: mixed (binary-analysis of the pinned image: Ghidra 12.2, llvm-objdump, its own .pdata, EH, RTTI, POGO and relocation data; community-headers; community name databases)
Sources and immutable revisions / licenses: CharmedBaryon/CommonLibSSE-NG `b93280e832f263dbef44e44cbe2936622a02f91a` (MIT); powerof3/CommonLibSSE `654e55f7979c1733033d5dbef176e43827bac944` (GPL-3.0; files carrying its declarations state GPL-3.0); Address Library 1.7.104.0 SHA-256 `8aab3dd251d135b849bd983f86a4a205c920fa3e81f8e30c0e63ccfef9423842`; meh321's name list
`skyrimae.rename` SHA-256 `8becdeae9fd2a7cc2ecb95fd0158718ca618a9cf10cff25d24e444f102abdf90`, used with the author's
permission as reported by the maintainer (`docs/authorizations.md`).
Name provenance: COMMUNITY (unverified), class names EXE_RTTI
Confidence: high for counts, sizes, slot tables and checks; medium for class attribution; low to medium for names

## Question and method

Which functions should the next Drafter batch take, now that every approved naming source can be
checked against the image? `tools/ghidra/build_function_table.py` (27 s with cached Ghidra and
disassembly passes; the Ghidra pass adds 35 s) writes a private row per Ghidra entry (kind, v2 verdict
by the exporter's `classify`, owner class, names per source, EH facts, callers, callees, L1/L2 keys)
and a row per class with a primary vftable (found from CompleteObjectLocators through relocations).
A slot function belongs to the most basic class holding it at that slot; object size is the operator
delete size in the class's own slot 0. NG and po3 are checked per class as `docs/resource-guidelines.md`
section 2 asks (C1, C2, C3 with at most 10% deviating slots, C4 where asserted), plus the RTTI name of the
`VTABLE_` id and the first base; slot names come only from passing classes, deviating slots get none;
meh321 names count unless a placeholder or outside the hierarchy holding the function. `export_pack.py
plan --order fanin` keeps ordinary, v2-ready (supported, or cautioned only for a padded leaf or funclet
references), named functions of passing non-template classes with a prefix area, not middleware and
not in the inventory; ranks classes by summed fan-in, picks by fan-in then size, one per L1 cluster, at
most 500 B, plus 20 C++ EH functions with at most 3 states and no try block. Classes with an accepted
unit (Actor, NiTimeController) are left out so no record is re-opened.

## Observations

- Kinds: 89,973 ordinary (20.61 MB), 67,911 EH funclets, 9,762 initializers, 6,508 teardown, 1,847
  thunks. v2: 43,249 supported, 44,795 caution, 1,929 unsupported (1,240 unnamed EH handler, 748 jump tables).
- Classes: 7,390 primary vftables; size read for 6,897; 1,104 pass for at least one source (NG 880 of
  1,028 joined, po3 1,017 of 1,225). Of 83,873 slots, 54,299 get an NG name, 9,587 po3, 568 meh321.
- Ordinary functions with a usable name per source: NG slot 9,164; NG id 573; po3 slot 2,041; po3 id
  881; meh321 11,474; any 16,988. Before the checks the slot joins named 11,941 (NG) and 3,982 (po3).
- Owner: vftable 26,522, secondary 2,093, community id 831, meh321 9,233; neighbourhood guess 7,282; none 44,012.
- Eligible now (v2-ready, named, class passes, prefix area): 3,555 functions, 689 KB, in 418 classes;
  by size <=32 B 1,188, 33-64 494, 65-128 577, 129-256 587, 257-512 397, >512 312; 796 have C++ EH.
  Rejected: no usable name 65,693; v2 8,303; class fails checks 6,626; no vftable 2,374; no prefix rule
  2,339. Call-site census: 332,713 direct call sites over 36,879 callees.

| class | area | functions / bytes | C++ EH | name sources | checks passed | size |
|---|---|---|---|---|---|---|
| TESObjectREFR | forms | 14 / 1,958 | 7 | meh321 8, NG id 3, po3 id 1, po3 slot 2 | po3 | 0xA0 |
| TESForm | forms | 9 / 972 | 2 | meh321 4, NG slot 4, po3 id 1 | NG, po3 | - |
| TESObjectCELL | forms | 10 / 1,141 | 3 | meh321 5, NG id 2, po3 slot 3 | po3 | 0x148 |
| TESNPC | forms | 8 / 1,056 | 1 | meh321 3, NG id 3, NG slot 2 | NG, po3 | - |
| TESWorldSpace | forms | 9 / 1,437 | 2 | meh321 2, NG slot 6, po3 id 1 | NG, po3 | 0x358 |
| BGSDefaultObjectManager | forms | 7 / 432 | 1 | meh321 5, po3 slot 2 | po3 | 0xD38 |
| BGSLoadGameBuffer | forms | 3 / 173 | 0 | meh321 1, NG id 1, NG slot 1 | NG, po3 | 0x28 |
| TESGrass | forms | 7 / 112 | 0 | NG slot 7 | NG, po3 | 0x78 |
| NiObject | netimmerse | 7 / 250 | 0 | meh321 2, NG slot 5 | NG, po3 | 0x10 |
| NiAVObject | netimmerse | 8 / 1,240 | 1 | meh321 5, NG id 1, NG slot 2 | NG, po3 | 0x110 |
| NiNode | netimmerse | 8 / 1,397 | 1 | NG id 1, NG slot 7 | NG, po3 | 0x128 |
| NiInterpolator | netimmerse | 6 / 109 | 0 | NG slot 6 | NG, po3 | 0x18 |
| NiPSysModifier | netimmerse | 7 / 739 | 0 | NG slot 7 | NG, po3 | 0x30 |
| NiExtraData | netimmerse | 4 / 255 | 0 | NG slot 4 | NG, po3 | 0x18 |
| NiObjectNET | netimmerse | 6 / 849 | 0 | meh321 1, NG slot 5 | NG, po3 | 0x30 |
| BSShaderProperty | bsengine | 7 / 532 | 0 | NG id 2, NG slot 5 | NG, po3 | 0x88 |
| BSTempEffect | bsengine | 7 / 455 | 0 | meh321 1, NG slot 6 | NG, po3 | 0x30 |
| BSResourceNiBinaryStream | bsengine | 6 / 540 | 1 | NG id 1, NG slot 5 | NG, po3 | 0x38 |
| BSLightingShaderMaterialBase | bsengine | 8 / 1,830 | 1 | NG slot 8 | NG, po3 | 0xA0 |
| Character | actors | 7 / 373 | 0 | meh321 3, po3 slot 4 | po3 | 0x2B8 |

Total 148 functions, 15,850 B (46 <=32 B, 22, 31, 34, 15 up to 512 B); median 7 callers; EH all 1 state.

## Interpretation and alternatives

Slot comments are the largest checked source, meh321 the largest id source. A failing class may only
simplify the hierarchy; it needs an Engineer look, not a ban.
## Reproduction and sanitized evidence

`build_function_table.py --write-scope data/scope.json`; `export_pack.py plan --order fanin --label
fourth-batch --classes 20 --total 150 --task-prefix batch4-` (both in `tools/ghidra/`). Outputs private.

## Negative results and limitations

Census counts are lower bounds (pass-through registers are invisible). C5 is per function, not
checked here. Two unnamed EH handlers keep 1,240 functions unsupported until the private config names
them. Rows are not in `data/progress.json`; the private `inventory-rows.json` holds them.

## Reviewer and outcome

Not reviewed.
