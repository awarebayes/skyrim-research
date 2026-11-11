# Finding: compiler and toolset candidates for the pinned target

Status: HYPOTHESIS (header facts OBSERVED; toolchain identity INFERRED)
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), run locally; no game file or
part of one was uploaded. Only public version numbers were used in web lookups.
Date (UTC): 2026-11-11
Target build id / image SHA-256: `sse-steam-1-7-104` /
`846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f` (re-measured locally, equal)
Function RVA / size (if applicable): not applicable
Source exposure: binary-analysis (PE headers, Rich header, debug and load-config directories,
import DLL names only); public documentation
Sources and immutable revisions / licenses: see "Sources" below
Name provenance: not applicable
Confidence: high for the measured header facts; medium for the first-choice toolset;
low for every compiler flag

## Question and method

Which Microsoft compiler generation, toolset build and settings most likely produced the pinned
`SkyrimSE.exe`, and what alternatives remain? Paper research only: no compiler was installed and
nothing was compiled (plan step 3, first checkbox; issue #3).

1. Located the operator's local copy of the pinned executable and confirmed its SHA-256 equals
   `image_sha256` in `builds/target.json`.
2. Parsed the PE headers with an original standard-library Python script (kept private under
   `.local/experiments/compiler-candidates/`). It reads the COFF and optional headers, the section
   table, the Rich header (with checksum recomputation), the debug directory (CodeView, VC_FEATURE
   and POGO records), the load configuration and the import DLL names with per-DLL counts. It
   prints no code bytes and no disassembly.
3. Decoded Rich `@comp.id` values against the public richprint table, and mapped toolset numbers
   with Microsoft's compiler-versioning page and Visual Studio 2017 release history.

## Observations (measured from the pinned file)

Headers:

- PE32+, AMD64, GUI subsystem (2). Optional header linker version **14.16**.
- OS version 6.0, subsystem version 6.0, image version 0.0.
- DLL characteristics: HIGH_ENTROPY_VA, DYNAMIC_BASE, NX_COMPAT, TERMINAL_SERVER_AWARE.
  GUARD_CF is **not** set.
- COFF timestamp 2026-08-24 16:24:38 UTC; all three debug entries carry the same timestamp.
  No REPRO debug entry is present.
- Nine sections in this order: `.text` (code), `.rdata`, `.data`, `.pdata`, a second section
  also named `.text` but with read/write initialized-data characteristics and about 6 KiB,
  `_RDATA`, `.rsrc`, `.reloc`, `.bind`. The entry point lies in `.bind`.
- Data directories present: IMPORT (in `.rdata`), IAT, RESOURCE, EXCEPTION (in `.pdata`),
  SECURITY (an Authenticode certificate table), BASERELOC, DEBUG, TLS, LOAD_CONFIG.
  No export, delay-import or CLR directory.

Rich header: present and its checksum recomputes correctly. 27 entries. Product ids are
decoded with the public richprint table; "not in table" is kept as such.

| tool (prodid) | build | objects | public-table label |
|---|---|---|---|
| Linker 14.x (0x0102) | 27054 | 1 | VS2017 v15.9.82 build 27054 |
| Cvtres 14.x (0x00FF) | 27054 | 1 | VS2017 v15.9.82 build 27054 |
| C++ 19.x (0x0105) | 27054 | 2341 | VS2017 v15.9.82 build 27054 |
| C++ LTCG 19.x (0x0109) | 27054 | 68 | VS2017 v15.9.82 build 27054 |
| C 19.x (0x0104) | 27054 | 6 | VS2017 v15.9.82 build 27054 (interpolated) |
| C++ 19.x | 27045 | 148 | not in table |
| C 19.x | 27045 | 10 | not in table |
| C++ 19.x | 26706 | 32 | not in table |
| C 19.x / MASM 14.x / Implib 14.x | 26706 | 10 / 5 / 4 | not in table |
| C++ 19.x | 25547 | 8 | VS2017 v15.4.5 (interpolated) |
| C++ 19.x | 24215 | 78 | VS2015 Update 3.1 |
| C++ 19.x | 23918 | 620 | VS2015 Update 2 |
| C++ 19.x / C 19.x | 23506 | 74 / 18 | VS2015 Update 1 |
| C 19.x / Implib 14.x | 27412 | 1 / 28 | not in table |
| Implib 14.x (0x0101) | 30145 | 3 | VS2019 v16.11.15 |
| Implib 9.0 (0x0093) | 30729 | 24 | VS2008 SP1 |
| Implib 8.0 (0x007B) | 50727 | 4 | VS2005 |
| CVTCIL C++ 8.0 (0x0081) | 50727 | 2 | prodid named for VS2005; build not in table |
| C 8.0 / Implib 8.0 | 40310 | 2 / 2 | Windows Server 2003 SP1 DDK (AMD64) (interpolated) |
| AliasObj 11.0 (0x00C7) | 41118 | 1 | prodid named for VS2012; build not in table |
| Resource (0x0097) | 0 | 2 | resource |
| prodid 0x0001 | 0 | 606 | table: unmarked objects |

Counts derived from that table: 2415 compiled objects are build 27054 (2341 C++, 68 C++ LTCG,
6 C); 1003 compiled objects come from other builds. The prodid 0x0001 count (606) equals the
number of imported functions in the import table (606 across 32 DLLs).

Debug directory:

- CODEVIEW: an RSDS record naming a PDB with the executable's own base name, age 1. The build
  path's directory components are not published.
- VC_FEATURE: pre-VC11 objects 0, C/C++ objects 3414, `/GS` objects 509, `/sdl` objects 0,
  `/guard:cf` (guardN) objects 43.
- POGO: signature `LTCG`, 49 section-group records. Group names are standard MSVC/CRT
  contributions: `.text$mn`, `.text$mn$00`, `.text$x`, `.text$di`, `.text$yd`, `.xdata$x`,
  `.CRT$X*`, `.rtc$*`, `.tls*`, `.00cfg`, `.idata$*`, `_RDATA` and similar.

Load configuration: size 256 (field and directory agree). Security cookie pointer set.
Guard CF check-function pointer set, Guard CF function count 0, GuardFlags `0x100`
(CF_INSTRUMENTED only).

Imports relevant to the runtime: `MSVCP140.dll`, `VCRUNTIME140.dll` and ten
`api-ms-win-crt-*-l1-1-0.dll` (Universal CRT) sets. No `VCRUNTIME140_1.dll`. Other imports are
OS, DirectX, input, audio, video and Steam API libraries.

Local install context: Steam's bundled redistributable folder is named `vcredist/2015`
(the shared 2015-and-later runtime family). This does not identify a toolset build.

## Interpretation and alternatives

### Fields that may describe the Steam wrapper rather than the game code

- The entry point, the `.bind` section, the section count, SizeOfImage and the optional-header
  checksum reflect the wrapped file and say nothing about the compiler.
- The second, read/write section named `.text` is unexplained. It may be wrapper-related or an
  ordinary linker section that was renamed; this was not investigated and is UNKNOWN.
- The Authenticode table was added after linking; it describes signing, not compilation.
- Evidence that the toolchain-bearing fields were **not** rewritten: the Rich checksum is valid
  (it covers the DOS header, stub and Rich entries); the optional-header linker version 14.16
  agrees with the Rich linker entry (build 27054, a 14.16 build per the public table); the
  imported-function count equals the Rich prodid 0x0001 count; the debug-entry timestamps match
  the COFF timestamp. This makes wrapper tampering of those fields unlikely, not impossible.
  No unpacking or removal of the wrapper was attempted.

### Toolset identity (inferred)

- **First choice: MSVC 14.16.27054 (cl 19.16.27054, Visual Studio 2017 version 15.9 servicing,
  platform toolset v141), x64-targeting compiler.** Medium confidence. Basis: the linker,
  resource converter and the largest group of objects (2415) carry build 27054; Microsoft maps
  linker/toolset 14.16 to VS 2017 15.9; the public Rich table labels 27054 as VS2017 15.9.82
  (and lists 15.9.83 under the same build). The link date (2026-08-24) is after the
  Microsoft-listed 15.9.82 release date (2026-08-11), which is consistent but not proof.
  The table does not catalogue 15.9.12–15.9.81, so build 27054 may have shipped earlier than
  15.9.82; the exact servicing release that first shipped it is UNKNOWN.
- The compiler revision (`_MSC_BUILD`, the fourth field) is not recorded in the Rich header and
  is UNKNOWN. The compiler host architecture (x86-hosted or x64-hosted x64 compiler) is UNKNOWN.
- Absence of `VCRUNTIME140_1.dll` is consistent with the v141 toolset: the FH4 frame handler that
  needs it arrived with the VS 2019 toolset. This weakly argues against a newer compiler for the
  bulk objects, but VS 2019+ can be configured not to use FH4 (low-weight evidence).
- Older builds in the image do not mean Bethesda compiled game code with them. They are most
  plausibly prebuilt static libraries, CRT startup pieces and import libraries (third-party
  middleware or SDK libraries). Which code is in which group is UNKNOWN from headers alone and
  needs step 2 (Ghidra) analysis. Alternatives for functions outside the 27054 group:
  - **A1: 14.16.27045** (an earlier 15.9 servicing build, inferred from its numeric position
    between the table's 15.9.11 build 27030 and 27054): 158 objects. Low-medium confidence.
  - **A2: VS 2015 Update 2 (19.00.23918)**: 620 objects, the second largest group. Also
    Update 3.1 (24215, 78) and Update 1 (23506, 92). Medium confidence that these are
    prebuilt libraries; low confidence about whose code they contain.
  - **A3: build 26706** (a 14.1x build numerically just before VS 2017 15.8.0's 26726;
    possibly a 15.8 preview; not in the table): 51 objects including MASM. Low confidence.
  - **A4: build 27412** (numerically between 15.9 and VS 2019 16.0's 27508): 28 import
    libraries and one C object, plausibly Windows SDK import libraries. Low confidence.
  - VS 2019 16.11.15 (30145), VS 2008 SP1, VS 2005, the Windows Server 2003 SP1 DDK and VS 2012
    entries are import libraries or tiny counts; they are not candidates for game code.
- These are **not** the same evidence as for older Skyrim SE releases or for Fallout: New Vegas;
  no assumption was carried over from those games.

### Codegen settings: first set to try and alternatives

All of these are inferences with low confidence unless marked. Headers cannot reveal most flags.

| setting | first try | alternatives | header evidence | what would distinguish later |
|---|---|---|---|---|
| CRT linkage | `/MD` | none credible | measured: imports MSVCP140, VCRUNTIME140, UCRT sets (high) | n/a |
| optimization | `/O2` | `/Ox`, `/O1` on some files | none | instruction selection, inlining and size of a reconstructed function |
| LTCG | no `/GL` for most objects | `/GL` for the 68 LTCG objects | measured: POGO signature `LTCG`, 68 LTCG C++ objects vs 2341 non-LTCG | functions in LTCG objects get cross-module inlining; start the pilot on a non-LTCG function |
| PGO | none | none observed | no POGO-instrumented prodids; signature is `LTCG`, not a PGO signature | n/a |
| buffer security | `/GS-` | `/GS` | measured: 509 of 3414 objects have `/GS`; owner of those objects unknown | presence or absence of a security-cookie check in a function's prologue/epilogue |
| `/sdl` | off | none | measured: 0 objects | n/a |
| control-flow guard | off for game code | `/guard:cf` on a few objects | measured: 43 objects, image not marked GUARD_CF, function count 0 | guard-check calls at indirect call sites |
| exception handling | `/EHsc` | `/EHa`, or EH off in some files | `.text$x`/`.xdata$x` groups show C++ EH data exists | unwind/state tables generated for a function with destructors |
| RTTI | `/GR` (default) | `/GR-` per file | not a header fact; community RTTI tables (CommonLibSSE family) suggest RTTI exists, unverified here | presence of RTTI complete-object locators for a class |
| floating point | `/fp:precise` (default) | `/fp:fast` | none | contraction and ordering of scalar SSE operations |
| instruction set | default SSE2 | `/arch:AVX`, `/arch:AVX2` | none | VEX-encoded instructions in a function |
| function-level linking | `/Gy`, link `/OPT:REF,ICF` | `/Gy-` | none | identical-COMDAT folding of trivial functions |
| inlining | `/Ob2` | `/Ob1` | none | whether small callees are inlined |
| debug info | `/Zi` | `/Z7` | measured: CodeView PDB record present | does not change code; affects only object metadata |
| subsystem version | linker default 6.0 | explicit `/SUBSYSTEM:WINDOWS,6.0` | measured 6.0, consistent with the x64 default | n/a |
| language standard | `/std:c++14` (v141 default) | `/std:c++17` | none | rarely changes codegen; only matters if a construct differs |

The comparator (plan step 4) and one pilot function (step 5) are what decide among these.
A non-LTCG function from the 27054 group is the right first target; LTCG functions should wait.

## How each candidate can be obtained legitimately (not downloaded)

- **VS 2017 15.9 / v141 (first choice and A1).** Microsoft distributes Visual Studio 2017 and
  "Build Tools for Visual Studio 2017" from the Visual Studio Older Downloads page, which states
  that older versions require an active Visual Studio subscription (my.visualstudio.com).
  Microsoft's 2017 release history lists every 15.9.x release but no fixed-version download per
  release; a current install delivers the latest 15.9 servicing release. Whether the latest
  15.9.x still contains cl 19.16.27054 is UNKNOWN and must be measured from the installed
  compiler banner and file hash. Newer Visual Studio installers also offer an optional v141
  (14.16) component; which 14.16 build it installs is UNKNOWN and must be measured, not assumed.
- **VS 2015 updates (A2).** Same subscription channel. These matter only if a pilot function
  turns out to live in the VS 2015-built groups.
- **Licence basis.** Use is governed by the licence terms shown at install (Visual Studio
  Community, Professional or Enterprise; Build Tools terms are tied to a Visual Studio licence).
  This worker did not read or assess those terms; the maintainer must record the licence basis
  under gate G4 before any remote install. A third-party script that fetches Microsoft packages
  does not change the licence basis and was not evaluated.
- **Host routes (plan step 3).** x64 Linux with Wine (for example a Boat machine): needs G3 and
  G4; MSVC 14.16 under Wine is unverified. Windows Arm VM on this Mac: x64 emulation of the
  VS 2017 toolset is unverified and installing a VM is out of scope. x64 Windows host: the
  natively supported platform for VS 2017, so it is the lowest-risk route for exactness if one is
  available. Whatever the route, record the `cl.exe`/`link.exe` hashes and banners and confirm
  build 19.16.27054 before any comparison.

## Reproduction and sanitized evidence

```sh
shasum -a 256 '/path/to/Skyrim Special Edition/SkyrimSE.exe'   # must equal image_sha256
python3 -I .local/experiments/compiler-candidates/pe_meta.py \
  '/path/to/Skyrim Special Edition/SkyrimSE.exe' > .local/experiments/compiler-candidates/pe_meta.json
python3 -I .local/experiments/compiler-candidates/lookup_rich.py \
  .local/experiments/compiler-candidates/pe_meta.json /path/to/richprint/comp_id.txt
```

The scripts and their output are private under `.local/`. Published here: version numbers,
product ids, object counts, flag counts, section and DLL names. No bytes or disassembly.

## Sources

Accessed 2026-11-11.

- Microsoft, "Microsoft C++ (MSVC) compiler versioning",
  <https://learn.microsoft.com/en-us/cpp/overview/compiler-versions> (page git commit
  `e1708c80585b0c1aaa70e57190cd04b4779602ab`): VS 2017 15.9 = `_MSC_VER` 1916 = toolset 14.16.
  Microsoft documentation, cited only.
- Microsoft, "Visual Studio 2017 Release History",
  <https://learn.microsoft.com/en-us/visualstudio/releasenotes/vs2017-relnotes-history>
  (page git commit `e17d9485a84e5df91c818532ee0c75d3e04432c6`): 15.9.82 released 2026-08-11,
  15.9.83 2026-09-08, latest 15.9.85 2026-11-10. Cited only.
- Microsoft, "Visual Studio 2017 release notes",
  <https://learn.microsoft.com/en-us/visualstudio/releasenotes/vs2017-relnotes>: confirms 15.9.x
  servicing list; gives no 27054 mapping. Cited only.
- Microsoft, "Visual Studio Older Downloads", <https://visualstudio.microsoft.com/vs/older-downloads/>:
  older versions require an active Visual Studio subscription. Cited only.
- dishather/richprint `comp_id.txt`,
  <https://github.com/dishather/richprint/blob/b0a4f598cc076a8c2ff4b1b90850004bc17da31c/comp_id.txt>:
  community Rich `@comp.id` table. Used locally for lookups; nothing copied into this repo
  beyond the individual version labels quoted above. Licence not assessed.
- CharmedBaryon/CommonLibSSE-NG README at `b93280e832f263dbef44e44cbe2936622a02f91a`,
  <https://github.com/CharmedBaryon/CommonLibSSE-NG>: states VS 2022 / C++23 for building plugins
  and says nothing about the game's own compiler, so it gives no evidence here. MIT at review time.

## Negative results and limitations

- No compiler was installed or run; nothing here shows that any candidate reproduces game code.
- Build numbers 27045, 26706, 27412 and 41118 are absent from the public table; their mapping is
  numerical inference only.
- The VC_FEATURE C/C++ object count (3414) differs slightly from the Rich compiled-object total
  (3418 including CVTCIL); the reason is UNKNOWN.
- VC_FEATURE reports 0 pre-VC11 objects although the Rich header lists two C objects from a
  2005-era compiler; the reason is UNKNOWN.
- Which object groups contain Bethesda code versus middleware is UNKNOWN from headers.
- No assertion is made about older or newer Skyrim builds; addresses and toolsets must not be
  transferred between builds without proof.
- The public Rich table is a community resource; its labels were not independently verified
  against Microsoft binaries in this task.

## Reviewer and outcome

Pending maintainer review.
