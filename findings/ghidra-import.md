# Finding: Ghidra import of the pinned target and community mapping availability

Status: OBSERVED (import and analyzability); HYPOTHESIS (type-size agreement interpretation)
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), run locally; no game file
or game-derived output was uploaded to any service
Date (UTC): 2026-11-11
Target build id / image SHA-256: `sse-steam-1-7-104` /
`846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f` (re-measured locally before import; equal)
Function RVA / size (if applicable): not applicable; anchor RVAs below
Source exposure: mixed (binary-analysis of the pinned image; community-headers via a type archive)
Sources and immutable revisions / licenses:
- Ghidra 12.2 (upstream tag `Ghidra_12.2_build`, commit `8ca9077040cc43cd790babcfccf19475622a3e9a`),
  Apache-2.0, installed as Homebrew bottle `ghidra--12.2.arm64_tahoe.bottle.1`
  (sha256 `cee537edc3ede3db751094a5eb02716250d64c78b8036d0ccc2d5b6f2870f8f5`; formula source tarball
  sha256 `ade4fd6e277a10c82db4e75ff5acaeedb3113ef0c7d126ea2c8b38c37128f3c3`).
- OpenJDK 25.0.5.0.3 (Homebrew `openjdk@25`, bottle sha256
  `8dcb068655f82c9418265c58313178f291b27e75f0d653b41a7ea8cc172480da`), GPL-2.0 with Classpath exception.
- ByteBard97/skyrim-re-toolkit release `gdt-2026-08-29` (tag commit
  `6e3b58a9520129e9fec17f2dadf2b070af811bd4`), MIT: `CommonLibSSE_AE_b93280e.gdt`
  (sha256 `a2aaf7c92fffeccc323da7fb70938d474a9d3fdacab8046ce6f5bd9932ba16af`) and `coverage_baseline.json`
  (sha256 `a340e163b43154f3d5ef5bbaff35cbcd2d3e4a9b8326be1a367615f568e0fcf6`). Both digests equal the
  release's published digests. Runtime variant: AE.
- CharmedBaryon/CommonLibSSE-NG at `b93280e832f263dbef44e44cbe2936622a02f91a`, MIT (the archive's
  source; also consulted directly for `FormType` values in `include/RE/F/FormTypes.h`).
- Version-support references only, nothing imported: ianpatt/skse64 at
  `25b72352adb6543fa6d0bd3795780672b2e238e0` (`skse64_common/skse_version.h`);
  powerof3/CommonLibSSE `dev` at `654e55f7979c1733033d5dbef176e43827bac944` (GPL-3.0,
  `include/SKSE/Version.h`).
Name provenance: EXE_RTTI for class names located in the image, cross-referenced to COMMUNITY
(CommonLibSSE-NG) declarations of the same names; no function names are asserted
Confidence: high for import/analyzability observations; medium for the size agreements listed as
supported; low for the `FormType` interpretation

## Question and method

1. Can the pinned image be imported and auto-analyzed in Ghidra on Apple Silicon macOS, and is its
   main code analyzable as installed?
2. Is there a community address mapping for 1.7.104.0 that can be obtained with a clear licence?
3. Do community type declarations agree with independent evidence in this image?

Method: installed Ghidra and its required JDK through Homebrew. Ghidra 12.2's Getting Started notes
require JDK 25 and list macOS ARM 64-bit as supported. Checked the image hash against
`builds/target.json` and imported it headless (`analyzeHeadless`, `x86:LE:64:default`, compiler spec
`windows`) with all default analyzers. No PDB was supplied, and no symbol server was configured or
contacted. Afterwards, read-only Ghidra scripts reported counts, RVAs and integers only. Section
entropy came from a standalone script over the file's raw section data.

Type checks: for each class, the primary vftable is the RTTI-named `vftable` whose Complete Object
Locator offset field is 0. Constructor candidates are the functions that reference that vftable.
For each call to a candidate, and each vftable reference inside one, the script collected immediates
loaded into RCX/RDX before an earlier call within 32 preceding instructions. Each value counts once
per site. These counts were compared with the archive's structure size. Manual local inspection of
the TESObjectWEAP and TESNPC sites (kept private) was consistent with the counted constant being an
allocation size whose result is then passed to the constructor candidate.

## Observations

Import: analysis completed and the project saved (headless exit 0). The reported analysis time was
541 s on a 12-core Apple Silicon machine with a 10 GiB heap. There were 176,587 functions, 175,998 of
them in the main `.text`, and Ghidra recorded no Error bookmarks.

Section layout (RVA, virtual size, entropy over raw data; no content published):

| section | RVA | vsize | flags | entropy (bits/byte) |
|---|---|---|---|---|
| `.text` | 0x1000 | 0x17c64e8 | code, exec, read | 6.43 (5.73–6.49 per MiB) |
| `.rdata` | 0x17c8000 | 0x8ad254 | read | 5.07 |
| `.data` | 0x2076000 | 0x1625088 | read, write | 4.94 |
| `.pdata` | 0x369c000 | 0x1662d8 | read | 6.91 |
| `.text` (second) | 0x3803000 | 0x1908 | read, write, not exec | 2.62 |
| `_RDATA` | 0x3805000 | 0x6e0 | read | 6.52 |
| `.rsrc` | 0x3806000 | 0x92b10 | read | 2.25 |
| `.reloc` | 0x3899000 | 0x5592c | read, discardable | 5.47 |
| `.bind` | 0x38ef000 | 0x39248 | exec, read | 7.96 |

- The entry point (RVA 0x38ef310) is in `.bind`, the Steam wrapper section. `.bind` is near-random
  (7.96 bits/byte); Ghidra formed 3 functions there. It was not examined further.
- The main `.text` is not near-random. Its exception table (`.pdata`) has 122,538 entries: 122,258
  begin in an executable block, 122,213 begin on a decoded instruction, 122,125 lie inside a function
  and 93,686 are function entry points. The rest are presumed chained/funclet entries; not examined.
- The import and IAT directories lie in `.rdata` (import directory size 0x294, implying 32 DLL
  descriptors). TLS callbacks are listed in `.rdata`.
- RTTI: 8,136 type descriptors, 8,637 complete object locators and `vftable` symbols, 7,393 classes
  with at least one vftable.

Mapping availability (step 5):

- 1.7.104.0 is a real runtime in community code: SKSE64 at the revision above defines
  `RUNTIME_VERSION_1_7_104` as its current release runtime, and powerof3/CommonLibSSE and
  alandtse/CommonLibVR (`ng`) define `RUNTIME_SSE_1_7_104`.
- Address Library for SKSE Plugins is distributed on Nexus Mods (mod 32444). The page returned
  HTTP 403 to automated fetch, downloads need a Nexus account that this session does not have, and
  the file permissions were not reviewed. **Not obtained; no 1.7.104 database was examined.**
- meh321/AddressLibraryDatabase (`0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91`) has no licence file. It
  was not downloaded, and its coverage of 1.7.104 is unknown.
- SKSE64's `skse64_license.txt` contains only a use exclusion and no general grant. Its source
  offsets were not used.
- CommonLibSSE-NG at `b93280e` targets AE up to `RUNTIME_SSE_1_6_1330`, not 1.7.x. The toolkit archive
  is built from it. CommonLib addresses are Address Library IDs, which need the per-version database.
- **No licensed address mapping (ID→RVA or name→RVA) for 1.7.104.0 was obtained. No community
  function address was applied or checked.**

Type-level anchors (`sse-steam-1-7-104`; class names from EXE_RTTI matching CommonLibSSE-NG names;
archive size from `CommonLibSSE_AE_b93280e.gdt`, whose baseline marks each listed size `OK` against
the header's own `static_assert`):

| class | primary vftable RVA | archive size | sites with that constant / sites with any | result |
|---|---|---|---|---|
| TESObjectWEAP | 0x181a620 | 0x220 | 3 / 3, top value | size agrees |
| TESNPC | 0x185ec20 | 0x268 | 6, top value | size agrees |
| TESWorldSpace | 0x182c120 | 0x358 | 3, top value | size agrees |
| EnchantmentItem | 0x17e1aa0 | 0xc0 | 3 | size agrees |
| TESObjectMISC | 0x1818860 | 0x100 | 4 | size agrees |
| AlchemyItem | 0x17df570 | 0x168 | 3 | size agrees (weak) |
| IngredientItem | 0x17e22d0 | 0x140 | 2 | size agrees (weak) |
| ScrollItem | 0x17e52b0 | 0x168 | 2 | size agrees (weak) |
| SpellItem | 0x17e5a08 | 0xe8 | 2 | size agrees (weak) |
| TESObjectARMO | 0x1816580 | 0x228 | 1 | single site; weak |
| TESQuest | 0x1860910 | 0x268 | 1 | single site; weak |
| TESRace | 0x1861d68 | 0x4b8 | 1 | single site; weak |
| TESObjectBOOK | 0x1816de0 | 0x138 | 0 | inconclusive: callers are short stubs |
| TESObjectLIGH | 0x18140f0 | 0x130 | 0 | inconclusive |
| TESAmmo | 0x180fc30 | 0x128 | 0 | inconclusive |
| BGSKeyword | 0x1855e20 | 0x28 | 0 | inconclusive |
| PlayerCamera | 0x196d980 | 0x168 | 0 | inconclusive (singleton allocation not found) |
| MenuControls | 0x197c1e8 | 0x88 | 0 | inconclusive |
| ActiveEffect | 0x18f5b98 | 0x90 | 19 (0x98: 22, 0x768: 24) | ambiguous: derived classes share sites |
| TESCamera | 0x18ebbe0 | 0x38 | 0 (0x18: 3) | not supported; unexplained |

Full vftable slot counts agree with the archive's vtable struct for root classes, where that
struct lists the full table: TESForm 59/59, ActiveEffect 25/25, TESCamera 3/3, BSExtraData 3/3. For
derived classes the archive's `<Class>_vtable` structs list only overridden or added methods, so
their counts cannot be compared with the image's full tables. No claim is made for them.

Constants equal to CommonLibSSE-NG `FormType` values for the same class recur at these sites:
ARMO 0x1A (11), BOOK 0x1B (10), INGR 0x1E (9), LIGH 0x1F (8), MISC 0x20 (9), AMMO 0x2A (10),
ALCH 0x2E (7), SPEL 0x16 (9), ENCH 0x15 (4).

RTTI absences: no vftable was found for UI, BSInputDeviceManager, TESDataHandler or ConsoleLog. This
was not investigated. One possibility is that these classes are not polymorphic.

## Interpretation and alternatives

Outcome **(b): code is analyzable as installed, but community address mappings for this build are
missing.** The main `.text` decodes cleanly at almost every exception-table entry, and RTTI is intact.
The image did not need unpacking, dumping or modification. Only the wrapper section is high-entropy.

The type checks are **layout-size agreement**, not verified field offsets, names or address
mappings. They suggest that, for the supported classes, the AE archive's total sizes still hold on
1.7.104. Alternatives: an allocation constant could belong to a different object that shares the
constructor, or a matching size could hide internal layout changes. The `FormType` agreement is
consistent with the enum values being unchanged on this build, but what the constant is passed to is
a guess (low confidence).

## Reproduction and sanitized evidence

Pinned tools: Homebrew `ghidra` 12.2 (rebuild 1) with `openjdk@25` 25.0.5.0.3 on arm64 macOS 26.2.

```sh
# Ghidra rejects project paths that contain a dot-prefixed element such as .local,
# so a dot-free symlink outside the repository points at .local/analysis.
ln -sfn "$PWD/.local/analysis" "$HOME/ghidra-links/skyrim-research"
.local/experiments/ghidra-import/run-import.sh '/path/to/SkyrimSE.exe'   # refuses a hash mismatch
# Then the read-only survey scripts in .local/experiments/ghidra-import/scripts/
# (ImportSurvey.java, AnchorSurvey.java) via analyzeHeadless -process -noanalysis -readOnly.
```

Private evidence: `.local/experiments/ghidra-import/` (section survey, survey and anchor outputs,
logs) and the project under `.local/analysis/`. No bytes, disassembly or decompiler output published.

## Negative results and limitations

- No 1.7.104 Address Library database was available under the gates and licences in force. No
  community function or variable RVA was checked. Checks that need a mapping (string-referencing
  functions, mapped vtables, named globals) were not possible.
- Only one runtime variant of the type archive (AE, CommonLibSSE-NG `b93280e`) was used. It predates
  1.7.x support in that fork. The archive's own baseline marks most classes unverified; only `OK`
  classes were used.
- The allocation-site heuristic can miss allocations (stub callers, factory tables, inlined
  constructors) and can count unrelated constants. Zero counts are not evidence of disagreement.
- Ghidra's function count and `.pdata` agreement show that decoding succeeded. They do not show that
  every function boundary or the decompilation is correct.
- One analysis run only; it has not been reproduced by a second person or host.
- Installing Ghidra through Homebrew also upgraded shared formulae on the host (harfbuzz, jpeg-turbo,
  webp, xz, libtiff, little-cms2; icu4c@79 installed).

## Reviewer and outcome

Pending maintainer review.
