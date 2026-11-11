# Finding: MSVC 19.16.27054 compiler worker on a Boat machine under Wine (synthetic pilot)

Status: OBSERVED (worker reproduces synthetic builds; no game comparison was made)
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5); task p2-boat-pilot
Date (UTC): 2026-11-11
Target build id / image SHA-256: not applicable. Nothing was compared against `sse-steam-1-7-104`
or any other game file. The comparator ran against a synthetic DLL built in this pilot.
Function RVA / size (if applicable): not applicable (synthetic functions only)
Source exposure: black-box (original synthetic code and public tools only)
Sources and immutable revisions / licenses: see "Tools and pinned inputs"
Name provenance: not applicable
Confidence: high for the measured versions, hashes and results below; this establishes a
build worker, not that this is the compiler used for the target (see limitations)

## Question and method

Plan step 3 (hands-on part), issues #3 and #4; AGENTS.md phase 2. Can one Boat `default`
machine run the first-choice toolset from `findings/compiler-candidates.md` (VS 2017 15.9,
v141, cl 19.16.27054, x64) under Wine, compile original synthetic C++ deterministically, and
feed real MSVC output to the repository comparator (`tools/compare.py`, contract v1)?

1. Read msvc-wine at a pinned commit before running it (ISC licence; scripts only, the
   downloaded tools are not covered). `vsdownload.py` reads Microsoft's installer manifest,
   downloads payloads from the URLs it lists and checks each against the manifest SHA-256.
   A dry selection run on the operator's Mac fetched only the manifest.
2. Created one Boat machine with no account environment secrets (`boat new --no-env`) and a
   2-hour auto-stop, copied in only `tools/compare.py`, `tools/pecoff.py` and `tools/verifier/`,
   and ran `tools/verifier/setup_boat_machine.sh`.
3. Built the synthetic sources twice (builds A and B, separate fresh directories), then a third
   time five seconds later (C) and a fourth time with a second, independent install (D).
4. Attributed every differing byte between builds to named fields
   (`tools/verifier/pilot_compare.py determinism`).
5. Ran the comparator on object A against image B for five functions plus three negative
   cases (`pilot_compare.py compare`), on the machine and again on the operator's Mac.

## Tools and pinned inputs

| item | value |
|---|---|
| Boat CLI | 1.0.97 |
| machine | one `default` machine (4 vCPU, 8 GB, 79 GB root disk), provider `baremetal`; created 2026-11-11 19:58:10 UTC; auto-stop deadline 21:58:10 UTC; stopped 20:04:58 UTC |
| OS / kernel / CPU | Ubuntu 24.04.4 LTS; Linux 6.8.0-117-generic x86_64; AMD Ryzen 7 9700X (as reported by the guest) |
| Wine | `wine-9.0 (Ubuntu 9.0~repack-4build3)`; packages `wine`, `wine64`, `libwine` 9.0~repack-4build3 from the Ubuntu noble archive |
| other packages | msitools 0.103+repack-1build3, libgcab-1.0-0 1.6-1build2, winbind 2:4.19.5+dfsg-4ubuntu9.8, python3 3.12.3-0ubuntu2.1 |
| msvc-wine | <https://github.com/mstorsjo/msvc-wine> commit `d8a499efde3e1bd1862e2bebac976640c5f4c1fe`; ISC licence (scripts only) |
| installer manifest | VS 2017 `15.9.85+37902.15` (`buildVersion` 15.9.37902.15), from `https://aka.ms/vs/15/release/channel`; pinned by its download URL; file SHA-256 `3f11dac605c9241ddb6b0ec8a374de97f778a75df93788e7e7ec417d1ea8ee17` (the channel's own `sha256` field for it is a different value and was not used) |
| package hosts | selected payloads come from `download.visualstudio.microsoft.com` (Microsoft) |
| licence acceptance | `vsdownload.py --accept-license`, accepting the Build Tools licence the manifest links (`https://go.microsoft.com/fwlink/?LinkId=831113`), on the basis recorded in `docs/authorizations.md` |
| package selection | `--major 15 --host-arch x64 --architecture x64 --with-default no --with-msvc yes --with-sdk yes --sdk-version 10.0.19041`: 41 packages, 747.9 MB download |
| toolset directory | `VC/Tools/MSVC/14.16.27023` (the directory name stays at the 15.9 release value; the binaries inside are newer) |
| compiler | `cl.exe` banner: `Microsoft (R) C/C++ Optimizing Compiler Version 19.16.27054 for x64`; x64-hosted, x64-targeting |
| linker | `link.exe` banner: `Microsoft (R) Incremental Linker Version 14.16.27054.0` |
| Windows SDK | 10.0.19041.0, the only SDK this manifest offers (msvc-wine's own 15.9 default, 10.0.17763, is not in it) |

Compiler binaries (`bin/Hostx64/x64`), also in `tools/verifier/pinned.sha256`:

| file | size (bytes) | SHA-256 |
|---|---|---|
| cl.exe | 427080 | `5d118b3d66dd574616ea5be3b74d20793a4f37a0fa067cf09c52388a8c492e7e` |
| c1xx.dll | 8396360 | `4d5f2f8c1ed3384ae15be5b31e2918e4a200913cb58374543b7a05762de234be` |
| c2.dll | 7223352 | `03627abf4cde10390bc086ba1a85625ed61c2708838db9fff0dc9830040bbf2b` |
| link.exe | 1711720 | `70e987473cc4c67f65cdcabb82b3dc4827cb9d224d6016843051363b4cacb099` |

Main Visual Studio packages installed (id, version): `Microsoft.VisualCpp.Tools.HostX64.TargetX64`
14.16.27054 (and its `.Resources` 14.16.27054); `Microsoft.VisualStudio.Component.VC.Tools.x86.x64`
15.9.28230.55; `Microsoft.VisualCpp.CRT.Headers` 14.16.27033; `Microsoft.VisualCpp.CRT.x64.Desktop`
14.16.27032; `Microsoft.VisualCpp.CRT.x64.OneCore.Desktop` 14.16.27023;
`Microsoft.VisualCpp.CRT.Redist.X64` 14.16.27052.3; `Microsoft.VisualCpp.Premium.Tools.HostX64.TargetX64`
14.16.27023; `Microsoft.VisualCpp.PGO.X64` 14.16.27023; `Microsoft.VisualCpp.CodeAnalysis.Extensions.X64`
14.16.27045; `Microsoft.Windows.UniversalCRT.Msu.7` 10.0.26624.1; `Win10SDK_10.0.19041` 10.0.19041.4;
plus the x86 CRT, store CRT, static analysis and resource packages the selection pulls in
(full list of 41 kept privately with the setup log). `vsdownload.py` warned that
`Microsoft.VisualCpp.Servicing.Redist` is absent from this manifest; it is a redistributable
props package and did not affect compilation.

**The compiler is cl 19.16.27054**, the build that the target's Rich header records for its
largest object group (`findings/compiler-candidates.md`). The servicing revision (fourth version
field) of the target's compiler is not recorded in the target, so equality of that field is
unknown; this is the 19.16.27054 that VS 2017 15.9.85's manifest ships today.

## Synthetic inputs and flags

Original sources in `tools/verifier/synthetic/` (no third-party code):

| function | exercises | size (bytes) | relocations | unwind |
|---|---|---|---|---|
| `pilot_mix` | integer arithmetic; leaf under 100 bytes, no calls | 11 | none | none (leaf) |
| `pilot_field` | struct field access through a pointer | 10 | none | none (leaf) |
| `pilot_branch` | conditional branch | 14 | none | none (leaf) |
| `pilot_scale` | global data read and write | 20 | 2 `REL32` (data) | none (leaf) |
| `pilot_call` | call to `pilot_scale`, branch around it | 44 | 1 `REL32` (call) | 1 `.pdata` entry, 8 bytes `UNWIND_INFO` |

`pilot_variant.cpp` defines `pilot_mix` with a different shift count for a negative test.

Compile: `cl /nologo /c /O2 /MD /GS- /EHsc /GR /fp:precise /Gy` (first-choice set from
`findings/compiler-candidates.md`, no `/GL`, no debug info in objects).
Link: `link /nologo /DLL /MACHINE:X64 /INCREMENTAL:NO /OPT:REF /OPT:ICF /DEBUG /MAP` into
`pilot.dll`. Each function is exported so `/OPT:REF` keeps it.

## Observations

### Install

`setup_boat_machine.sh` completed in about 2.5 minutes (apt, download, unpack, `install.sh`).
A second run on the same machine into fresh work and install directories exited 0 and its
compiler binaries matched `pinned.sha256` (`cl.exe`, `c1xx.dll`, `c2.dll`, `link.exe`: OK).
It was not re-run on a second, fresh machine.

### Determinism

| comparison | function code (all 5, by RVA and content) | DLL `.text`, `.data`, `.pdata`, `.reloc` | differing bytes, by field |
|---|---|---|---|
| A vs B (same second) | identical | identical | DLL: CodeView RSDS GUID (16 bytes), RSDS PDB path (1 byte: output directory name). Objects: `.debug$S` (1 byte), `.chks64` (8 bytes) |
| A vs C (+5 s) | identical | identical | as A vs B, plus 1 byte each in: COFF header TimeDateStamp (DLL and objects), debug directory TimeDateStamp of the CODEVIEW, VC_FEATURE and POGO entries; map file line `Timestamp is ...` |
| A vs D (second install) | identical | identical | same fields as A vs C |

Explanations, checked against the bytes privately:

- **COFF TimeDateStamp** (objects and DLL) and the three **debug directory TimeDateStamps**:
  the build time in seconds. A and B were built in the same second and so agreed.
- **CodeView RSDS GUID**: a fresh GUID per link, shared with the PDB. **RSDS PDB path**: the
  absolute PDB path, which differs by the output directory name.
- **Object `.debug$S`**: even without `/Zi` or `/Z7`, the object carries a small CodeView
  record naming the object file by absolute path; the one byte is the output directory name.
- **Object `.chks64`**: a table of one 8-byte checksum per section; the entry that changes is
  the one for `.debug$S`. Code-section checksums are equal.
- The `.rdata` section differs only because the debug directory and RSDS record are in it.
- The PDB differs as a whole file (GUID and timestamps); it was not decomposed.
- The install path (`msvc` vs `msvc2`) does not appear in the objects or the DLL.

### Comparator on real MSVC output

Inputs per case: object from build A; image `pilot.dll` from build B; task size from build B's
object section; RVAs from every symbol line of build B's linker map (216 names, 1 name listed at two RVAs and dropped so it cannot be used); a synthetic manifest
`build_id: synthetic-boat-pilot-b`, `status: pinned`, `image_sha256` of build B's DLL
(`a1064e2d40aa553cfdb717153f47e2a0d30b61f2f69df5a6d2c515e83f6c6945`); a recipe naming the
compiler hash, version and flags. `builds/target.json` was not used or changed. Comparator
0.1.0, `compare.py` SHA-256 `9c84133770124acbdb2ff20851ddb02692a3a75b06b210733c8b980a4ca60a1a`,
`pecoff.py` `2b165c8c9ea42565694bb5eda444c58df6c772030bdbdb9be431512ba50a7cd4`
(report `source_sha256` `da2180f0a93f3e1c9c19ea7164f5c7e7db968b872756023973630726cacb86e5`).

| case | result | reason | coverage |
|---|---|---|---|
| `pilot_mix` | pass | `all-checks-passed` | 11 exact; unwind none-in-range |
| `pilot_field` | pass | `all-checks-passed` | 10 exact; unwind none-in-range |
| `pilot_branch` | pass | `all-checks-passed` | 14 exact; unwind none-in-range |
| `pilot_scale` | pass | `all-checks-passed` | 12 exact + 8 by reference (2 `REL32`); unwind none-in-range |
| `pilot_call` | pass | `all-checks-passed` | 40 exact + 4 by reference (1 `REL32`); unwind covered, 1 entry, 8 bytes |
| variant source (`pilot_variant.obj`, `pilot_mix`) | fail | `code-byte-mismatch` | at +0x5; same length, so not a size rejection |
| wrong call target (map points `pilot_scale` at `pilot_mix`'s RVA) | fail | `relocation-target-mismatch` | `REL32` at +0x1d naming `pilot_scale` |
| wrong data target (map moves `?g_pilot_total@@3HA` by 8) | fail | `relocation-target-mismatch` | `REL32` at +0x2 naming `?g_pilot_total@@3HA` |

The same eight cases re-run on the operator's Mac (Python 3.14.6) from the copied outputs gave
identical results, reasons and coverage. On this input the comparator met no unsupported
feature: `/Gy` gave one `.text$mn` COMDAT per function, the only relocation types were `REL32`
in code and `ADDR32NB` in `.pdata`, and unwind info was version 1 without handlers.

## Interpretation and alternatives

- A Boat `default` machine with Ubuntu's Wine 9.0 runs the x64-hosted cl 19.16.27054 and
  link 14.16.27054 and produces code that is identical across clean builds and across two
  installs from the pinned recipe. Build-to-build differences are confined to timestamps,
  the PDB GUID and absolute paths. A future verifier must exclude or normalize only those
  named fields when comparing whole files; function comparison through the comparator is
  unaffected because it reads code bytes and unwind info only.
- The pilot is too simple to exercise contract features that real game functions will need:
  functions with exception handlers (`unsupported-unwind`), jump tables, `ADDR64` data
  references and `/GL` objects were not produced here. Expect those rejections on real input.
- Under Wine, `cl.exe` may differ in behavior from native Windows in ways these small inputs do
  not reveal (for example parallel or PDB-server paths); `/Zi` with `mspdbsrv` was not tested.

## Reproduction and sanitized evidence

```sh
# on a fresh x86-64 Ubuntu 24.04 machine holding only tools/compare.py, tools/pecoff.py, tools/verifier/
tools/verifier/setup_boat_machine.sh "$HOME/msvc"
tools/verifier/build_pilot.sh "$HOME/msvc" .local/pilot/a
tools/verifier/build_pilot.sh "$HOME/msvc" .local/pilot/b
python3 -I tools/verifier/pilot_compare.py determinism .local/pilot/a .local/pilot/b
python3 -I tools/verifier/pilot_compare.py compare .local/pilot/a .local/pilot/b \
  --work .local/pilot/compare --recipe .local/pilot/recipe.json
```

Generated objects, DLLs, PDBs, maps, setup logs, reports and comparator diagnostics are kept
privately under `.local/experiments/boat-pilot/`. They are synthetic but contain Microsoft
CRT/linker output and are not published.

## Negative results and limitations

- **Not a game comparison.** Nothing was compared with `SkyrimSE.exe`. No game file, slice,
  address database or analysis output was put on the machine.
- **Not proof of the original compiler.** Equal build numbers do not show equal servicing
  revisions, host architecture (the target's compiler may have been x86-hosted), libraries or
  flags. Only reconstructed-function comparisons can test that.
- Wine is the distribution package, pinned by version string only, not by binary hash.
  The Windows SDK files are verified by the manifest hashes during download but not pinned
  separately in the recipe.
- The pinned manifest is a Microsoft URL that may be withdrawn; the recipe then fails at the
  hash check instead of following the channel.
- The setup script was re-run on the same machine, not on a second fresh machine.
- Two harness bugs in `pilot_compare.py` were found and fixed during the run (it called the
  comparator in Python isolated mode, which broke its import; and its task ids contained
  underscores, which the contract rejects as `invalid-task`). The comparator and contract
  were not changed. Results above are from the fixed harness.
- Saved snapshots are not available on the Boat trial (`trial_saved_snapshots_not_allowed`),
  so no named snapshot exists. The stopped machine keeps Boat's automatic stop snapshot, which
  Boat documents as retained 14 days. Later machines must be rebuilt with the recipe.

## Cost

Boat trial included compute only. `trialComputeUsedSeconds` 16 before, 420 after; `boat usage`
for this machine: 404 seconds, `default` type, billing multiplier 1 ($0.00404 at the
listed rate, drawn from trial-included time). Wallet balance $0 before and after; no purchase,
pack, extra-starts or plan change; `hasPaymentHistory` false.

## Reviewer and outcome

Pending maintainer review.
