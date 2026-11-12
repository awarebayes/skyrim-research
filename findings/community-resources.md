# Finding: community resources ranked by how much they cut the cost per reconstructed function

Status: OBSERVED (licences, metadata, local counts); HYPOTHESIS (cost ranking, scope estimates)
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), task p5-resource-survey
Date (UTC): 2026-11-12 (all URLs below accessed on this date)
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): not applicable
Source exposure: mixed (public repositories and web pages; local counts over the pinned image, the
Address Library 1.7.104.0 database and the Ghidra export from `findings/ghidra-import.md`)
Sources and immutable revisions / licenses: in the table; licences read from the LICENSE/COPYING file
at the stated revision unless marked "API" (GitHub licence endpoint only)
Name provenance: not applicable (no names are published here)
Confidence: high for licences and measured counts; medium for estimates; low for the cost ranking

## Question and method

Which public resources would most reduce the cost per reconstructed function, and how far can scope
be narrowed? Repository metadata came from `gh api` and licence files from the repositories. Five
repositories or files were downloaded into `.local/experiments/resource-survey/` and counted with
original stdlib scripts. Nothing was vendored. Counts against the image use the Address Library
database (`versionlib-1-7-104-0.bin`, SHA-256 `8aab3dd2…9423842`) and the Ghidra export of 176,001
function entries. "Measured" means counted here. "Estimated" means derived with a stated heuristic.

Two joins were used. **Id join:** every `RELOCATION_ID(se, ae)`, `REL::RelocationID`, `REL::VariantID`
or `REL::ID(n)` in a tree is resolved through the 1.7.104 database. It counts when it lands on a Ghidra
function entry. **Vtable join:** slot comments (`// NN`) on `virtual`/`override` lines are attached to
the class named by that header's `VTABLE_` constant. They are applied to every EXE RTTI primary vftable
whose class or primary-base chain (from the EXE's own Class Hierarchy Descriptors) declares that slot.
The join then counts distinct function entries in those slots. Names are not checked by these joins.
Header slot numbers were written for SE/AE layouts. In 35 of 1,159 po3 classes, the header declares
more slots than the 1.7.104 vftable has, so each class needs a length check before use.

## Ranked table

Ranking is by expected reduction in cost per accepted function: names and types first, then scope
cuts that remove work, then tooling and method. Verdicts are by provenance and licence, not usefulness.

| # | resource (revision) | licence (file) | last activity | covers / maps to 1.7.104 | count | concrete use | verdict |
|---|---|---|---|---|---|---|---|
| 1 | [powerof3/CommonLibSSE](https://github.com/powerof3/CommonLibSSE) `dev` @ `654e55f7` | GPL-3.0 (`COPYING.txt`) | 2026-11-08 | SE+AE; defines `RUNTIME_SSE_1_7_104`; AE Address Library ids | **measured:** 888 id-named function entries (324 not in NG); vtable join names **14,227** distinct functions (10,075 of ≥16 B); 1,137 classes with slot comments, 7,528 slot declarations; 2,574 `static_assert(sizeof)` lines; ids hit 8,011 vftables | names, layouts, vtable orders, enum values; vtable join is the big lever | **use now** (maintainer approval in `docs/authorizations.md`) |
| 2 | Pinned image's own RTTI + Ghidra (local) | n/a (own copy) | — | exact build | **measured:** 8,637 vftables, 89,745 slots, 29,776 distinct functions referenced from vftables; 7,098 type-descriptor names; 121 anonymous-namespace hashes (70 shared by ≥2 types) | EXE_RTTI class names; vtable join target; translation-unit grouping (b) | **use now** (local; publish names only under existing rules) |
| 3 | [alandtse/skyrim_vr_address_library](https://github.com/alandtse/skyrim_vr_address_library) @ `b0086b5a` | MIT (`LICENSE`) | 2026-11-11 | `offsets-1-7-104.0.csv` = AE id→offset dump for 1.7.104; SE/AE/VR name CSVs | **measured:** offset CSV equals the Nexus database pair for pair (435,162 of 435,162); 2,433 function entries get a non-placeholder name from `se_ae.csv`, `1.5.97_comments.csv`, `database.csv` (2,104 beyond the CommonLib id union) | MIT-labelled id→offset table for published pairs; extra names | offsets: **use with a licence decision** (it is a dump of meh321's Nexus data relabelled MIT); names: **use with a licence decision** plus per-name identity checks (contributors' sources unrecorded) |
| 4 | [alandtse/CommonLibSSE-NG](https://github.com/alandtse/CommonLibSSE-NG) `ng` @ `8edac4d2` (GitHub parent lfrazer/CommonLibVR) | GPL-3.0-or-later with Modding and Linking exceptions (`COPYING.txt`, README "License"); relicensed from MIT | 2026-11-11 | SE/AE/VR; `RUNTIME_SSE_LATEST_AE` = 1.7.104 | **measured:** 1,081 id-named function entries (most of any tree; 205 unique); vtable join 14,622 (10,314 ≥16 B); 1,192 classes with slot comments | same as #1, plus the most current 1.7.x ids | **use with a licence decision** (approval names powerof3 only) |
| 5 | [meh321/AddressLibraryDatabase](https://github.com/meh321/AddressLibraryDatabase) @ `0379cb6f` (`skyrimae.rename`) | no licence file (all rights reserved) | 2025-05-28 | AE ids → names (crowd-sourced IDA exports, 1.6.317+) | **measured:** 42,259 entries; 14,604 function entries with a method name, 16,751 more with a class only (`Class::sub_*`, `FuncN_*`) | would be the largest single naming source | **do not use** for publication; ask the author for a licence. Name origins are unrecorded |
| 6 | Official zlib 1.2.7 and libpng 1.2.18 sources ([zlib](https://zlib.net/), [libpng](http://www.libpng.org/pub/png/libpng.html)) | zlib licence; libpng licence | upstream | version strings for both found in the image (measured) | function count not measured; estimated low hundreds | compile upstream with the pinned recipe, match, and mark as library code (FNV did this with zlib 1.2.1) | **use now** after confirming the release archives' licence files |
| 7 | [CharmedBaryon/CommonLibSSE-NG](https://github.com/CharmedBaryon/CommonLibSSE-NG) @ `b93280e8` | MIT (`LICENSE`) | 2024-09-04 | up to AE 1.6.1330; AE ids | **measured:** 581 id-named function entries; vtable join 6,205 (4,687 ≥16 B); 414 classes with slot comments | current MIT naming source | **use now** (in use) |
| 8 | Ghidra Function ID, bundled `vs2017_x64.fidbf` (Ghidra 12.2, [NSA/ghidra](https://github.com/NationalSecurityAgency/ghidra)) | Apache-2.0 | 2026-11-10 | VS2017 x64 static libraries | **measured:** about 630 functions carry non-placeholder names after the default import (CRT/library and import-stub names, excluding funclets and thunks) | tag statically linked CRT startup code out of scope | **use now**; the effect is small because the CRT is dynamic (c) |
| 9 | [encounter/objdiff](https://github.com/encounter/objdiff) @ `9aeec9cb` | Apache-2.0 (API) | 2026-10-19 | x86/x86_64 PC objects, MSVC demangling (README) | — | interactive per-function diff for Drafters and Engineers; never the verifier | **use now** as a local aid |
| 10 | [ianpatt/skse64](https://github.com/ianpatt/skse64) @ `25b72352` | `skse64_license.txt`: one use exclusion, no grant | 2026-09-06 | `CURRENT_RELEASE_RUNTIME` = 1.7.104; raw offsets | **measured:** 402 distinct raw offsets, 306 on function entries, 34 on vftables | independent cross-check of identities | **study only** (local cross-check; nothing published) |
| 11 | [TES5Edit/TES5Edit](https://github.com/TES5Edit/TES5Edit) `Core/wbDefinitionsTES5.pas` @ `b0e67b16` | MPL-2.0 (`LICENSE.txt`) | 2026-11-11 | plugin record formats (version-independent) | **measured:** 96 `wbEnum`, 161 `wbFlags` in the file | enum and flag names for record-loading functions (`Load`/`InitItem`) | **use now** as a cited reference for facts; copying text needs MPL notices |
| 12 | [niftools/nifxml](https://github.com/niftools/nifxml) @ `970a6238` | GPL-3.0 (`LICENSE`) | 2024-09-15 | NIF file format incl. Bethesda versions | **measured:** 555 `niobject`, 156 `struct`, 111 `enum`, 24 `bitflags` | field order and names for NIF stream load/save functions; file layout ≠ memory layout | **use with a licence decision** (GPL; approval covers powerof3 only) |
| 13 | [FNV](https://github.com/momusdigital/fnv_decomp) @ `91e1b6e8`, [fnvdecomp.com/how](https://www.fnvdecomp.com/how), [f3decomp.com/how](https://f3decomp.com/how) | FNV: `LICENSE` grants no licence, contributors included; README tags some names as from an Xbox 360 development-build PDB and Havok/Gamebryo source. F3: no source published | 2026-11-07 | other games (FNV PC 1.4.0.525, 32-bit, VC++ 2008; about 72% of functions in `/Od` units) | ~74,500 and ~64,000 functions; 96,537 tries at about 3 matches per 100. **measured** (`tools/build_fnv_index.py`, name and slot join to our tables): 806 of our functions share class and method name with an FNV function, 476 more only a derived slot position, which agrees with our slot name in 174 of 641 named pairs | FNV: names, declarations and code of the same-named sibling method and the class's accessors, adapted (packs list the file and line); method: size-tiered models, scripted boilerplate, `units.json`, bytes-based progress | FNV: **use now** by maintainer decision (`docs/authorizations.md`, Notes), labelled `SIBLING(...)`; never as evidence about this build. F3: **study only** (method) |
| 14 | [isledecomp/reccmp](https://github.com/isledecomp/reccmp) @ `a0f494c0` | AGPL-3.0 (`COPYING`) | 2026-11-10 | 32-bit, old MSVC; newer MSVC "in progress" (README) | — | `// FUNCTION: <module> <addr>` source annotations, vtable/variable checks, report aggregation | **study only** (ideas; no x64 support) |
| 15 | Sibling CommonLibs: [Ryan-rsm-McKenzie/CommonLibF4](https://github.com/Ryan-rsm-McKenzie/CommonLibF4) (MIT), [alandtse/CommonLibF4](https://github.com/alandtse/CommonLibF4) @ `15f504ea` (MIT), [libxse/commonlibsf](https://github.com/libxse/commonlibsf) @ `d7a15706` (GPL-3.0) | as stated (API) | 2025-11 to 2026-11 | other binaries; no Skyrim ids | not counted | shapes of shared base templates (BSTArray, BSFixedString, handles, BSTEventSink, NiPointer) | **study only** for layouts; never addresses |

Also assessed: [Ryan-rsm-McKenzie/CommonLibSSE](https://github.com/Ryan-rsm-McKenzie/CommonLibSSE) (MIT, last push
2023-07-20; superseded by #1/#4/#7); [qudix/commonlibsse-ng](https://github.com/qudix/commonlibsse-ng) (MIT, fork of
#4 at a pre-relicence point, 2026-03-10; not counted); [ByteBard97/skyrim-re-toolkit](https://github.com/ByteBard97/skyrim-re-toolkit)
@ `b5039b37` (MIT `LICENSE`; archives built from #7, already used); [alandtse/vr_address_tools](https://github.com/alandtse/vr_address_tools)
(MIT; scripts that produce #3); [powerof3/CLibUtil](https://github.com/powerof3/CLibUtil) (MIT, utilities, no RE data);
[decomp.me](https://github.com/decompme/decomp.me) @ `ca51d1b3` (MIT; `win32` platform is x86 only, MSVC 4.0 to 8.0 SP1;
**no 19.16 and no x64**: not usable); [asm-differ](https://github.com/simonlindholm/asm-differ) (Unlicense; x86 only "to limited
extent"); [threatrack/ghidra-fid-generator](https://github.com/threatrack/ghidra-fid-generator) (MIT, 2020; could build a FID database
from the pinned toolset's own static libs); [astrelsky/Ghidra-Cpp-Class-Analyzer](https://github.com/astrelsky/Ghidra-Cpp-Class-Analyzer)
(MIT, archived) and [cmu-sei/pharos](https://github.com/cmu-sei/pharos) OOAnalyzer (own licence): Ghidra 12.2 already recovers
RTTI. [Mixaill/FakePDB](https://github.com/Mixaill/FakePDB) (Apache-2.0): PDBs for debugging, not matching. [mstorsjo/msvc-wine](https://github.com/mstorsjo/msvc-wine):
ISC for the scripts only, which the `LICENSE.txt` says do not cover the downloaded tools (already used).
Script extenders for older games: [xNVSE/NVSE](https://github.com/xNVSE/NVSE), [llde/xOBSE](https://github.com/llde/xOBSE) and
[ianpatt/f4se](https://github.com/ianpatt/f4se) have no licence file the API detects, and
[jazzisparis/JIP-LN-NVSE](https://github.com/jazzisparis/JIP-LN-NVSE) is GPL-3.0. They target 32-bit Gamebryo-era binaries:
**study only**, mostly for NiTArray/NiTMap and visitor idioms. [OpenMW](https://github.com/OpenMW/openmw) (GPL-3.0) is a
different engine and only a behavioural contrast: **do not use** for layouts.
[UESP Tes5Mod file formats](https://en.uesp.net/wiki/Skyrim_Mod:Mod_File_Format) (CC BY-SA 2.5 per
[UESP copyright page](https://en.m.uesp.net/wiki/UESPWiki:Copyright_and_Ownership)): **use now** as a cited reference for record,
save and archive formats; quoted text needs attribution and share-alike.

Middleware. Havok offered "Havok Complete" for PC free for non-commercial use from 2008, as a binary-only download
without source ([MCV](https://mcvuk.com/development-news/havok-complete-now-freely-available/),
[Engadget](https://www.engadget.com/2008-02-23-havok-offers-pc-game-devs-havok-complete-for-free.html)). Whether it is still
offered, and which SDK version Skyrim links, were not established. No Havok or Scaleform source is legitimately public.
Autodesk's [Scaleform help](https://help.autodesk.com/cloudhelp/ENU/Scaleform-Help/cpp_ref/00004.html) publishes 4.x API
reference documentation only. Verdict: **study only** for API names (they must be labelled as such) and treat both libraries
as out of scope. Bink is imported from `bink2w64.dll` (measured: 32 imported DLLs, including `bink2w64.dll`, `steam_api64.dll`,
`d3dx9_42.dll`, `MSVCP140.dll`, `VCRUNTIME140.dll` and UCRT `api-ms-win-crt-*`), so no Bink code is linked. No
DirectXTK/DirectXTex, curl, OpenSSL or SQLite identification strings were found (measured; absence of strings is weak
evidence). An LZ4-named class exists in RTTI; its implementation version is unknown. No leaked material or unofficial PDB was
encountered or used. None is named here.

## Direct answers

**(a) Most named functions for 1.7.104 right now.** powerof3/CommonLibSSE is already approved. Its vtable slot comments,
joined to the EXE's RTTI vftables, name about **14,200 distinct function entries** (estimated by the vtable join; measured
counts, names unverified; 10,075 are ≥16 B). Its Address Library id tags name only **888** (measured), compared with 581 for
NG. alandtse's NG names slightly more (14,622 via vtables, 1,081 via ids) but needs a licence decision. The largest
crowd-sourced list, meh321's `skyrimae.rename` (14,604 method-named function entries, measured), has no licence. The vtable
join is already partly how the project names functions (`ArmorRatingVisitor` slot anchors); scripting it across all classes
is the cheapest next step. Each name also needs the per-class slot-count check described in Method.

**(b) Compilation units and source file names.** No public source maps Skyrim functions to translation units. Three local
signals exist. (1) MSVC anonymous-namespace RTTI names carry a per-file hash: the image has 121 such hashes, 70 shared by two
or more types (measured). Types with the same hash come from the same `.cpp`. Their vtables and constructors then mark that
unit. (2) The image contains 118 strings that look like source paths (`.cpp`/`.h` with a separator; measured). By path family,
about 60 belong to Havok, 5 to the Bethesda.net client, 4 to Scaleform and 49 to others. They come from assert or log macros,
and each function that references one belongs to that file. (3) Link order: MSVC places a unit's functions contiguously, so
runs of functions bounded by (1) and (2) approximate units. To mine these, run local Ghidra scripts over the private project.
Write `.local/` tables of RVA, signal kind and a salted hash or local id. Publish only counts and unit sizes. Publish a path
only after maintainer review, because the strings are game data. meh321's class-only names (16,751) would also group
functions by class, but they cannot be used.

**(c) Shrinking the ~176,000 total.** CRT/STL fingerprinting alone shrinks it little. The CRT is the dynamic UCRT/VCRUNTIME,
so only startup code is static. Ghidra's default import (FID and import names) named about 630 functions (measured), and std/Concurrency vftable windows hold
about 1,660 more (estimated). The large cuts are elsewhere (measured from Ghidra names; middleware by 256 KiB windows labelled
by majority vftable class family, estimated):

| category | functions | bytes | basis |
|---|---|---|---|
| EH unwind/catch funclets (`Unwind@`, `Catch@`), emitted with their parent | 67,896 | 989,869 | measured |
| import/jump thunks | 1,616 | 8,145 | measured |
| Havok (hk* vftable windows) | ~7,600 | ~1.95 MB | estimated |
| Bethesda.net client (`bnet` windows) | ~2,900 | ~0.47 MB | estimated |
| Scaleform (RTTI-bearing windows only; most GFx code has no RTTI) | ≥ ~800 | ≥ ~0.25 MB | estimated |
| std/CRT windows | ~1,660 | ~0.17 MB | estimated |
| unlabelled or mixed windows (holds the rest of Scaleform, zlib, libpng, CRT) | ~24,400 | ~3.5 MB | estimated |
| engine windows | ~70,700 | ~15.5 MB | estimated |

Excluding funclets and thunks leaves about 106,500 functions, which is a definitional change, not a reduction in work.
Excluding the identifiable middleware leaves roughly **71,000–95,000** game-code functions in scope (estimated: engine windows alone, up to engine plus all
unlabelled/mixed windows). By bytes, game code is about 15.5–19 MB of the 22.9 MB counted. Like FNV and Fallout 3, progress should be reported in bytes with an
explicit "in scope" denominator. A middleware exclusion needs an object-level classification (Rich-header groups,
`findings/compiler-candidates.md`) before any number is published as scope.

## Reproduction and sanitized evidence

```sh
E=.local/experiments/resource-survey; DB=/path/to/versionlib-1-7-104-0.bin; X=.local/experiments/address-mapping/image-export.txt
python3 -I $E/count_ids.py $DB $X /path/to/CommonLibSSE-NG /path/to/CommonLibSSE-po3 $E/clones/alandtse-ng
python3 -I $E/vtable_names.py /path/to/SkyrimSE.exe $X <trees...>
python3 -I $E/vraddr_names.py $E/dl-vraddr $DB $X $E/vraddr_realnamed.txt
python3 -I $E/middleware_est.py /path/to/SkyrimSE.exe $X
```

Outputs (`*.out`), the private string summary and the downloaded files are under `$E/`. The meh321 file was downloaded only
to count it.

## Negative results and limitations

- Joins check only that an id or slot lands on a function entry. They do not check identity. Slot names apply SE/AE header
  layouts to 1.7.104, and 35 po3 classes declare more slots than their vftable has.
- Middleware figures come from a window heuristic. Scaleform without RTTI and zlib/libpng are not separated.
- The quality of the names in #3 and #5 was judged from samples, not reviewed.
- The SKSE64 overlap with CommonLib was not measured. zlib/libpng function counts were not measured.
- Pages that refused automated fetch (UESP copyright page: HTTP 403) were cited from search results.

## Reviewer and outcome

Not reviewed. Licence decisions are needed for #3 (offset dump and names), #4, #12, and a request to meh321 for #5.
