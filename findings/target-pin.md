# Finding: identity of the pinned target executable

Status: OBSERVED
Author / human operator: awarebayes
AI assistance / model: Claude Code (claude-opus-5-5), run locally; no game file was uploaded
Date (UTC): 2026-11-11
Target build id / image SHA-256: `sse-steam-1-7-104` /
`846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): not applicable
Source exposure: binary-analysis (PE headers and version resource only)
Sources and immutable revisions / licenses: the operator's own Steam installation; `tools/fingerprint.py` at this commit
Name provenance: not applicable
Confidence: high for hash, store and file version; see limitations

## Question and method

Which executable is the research target, and how was its identity established?

1. Located `SkyrimSE.exe` in the operator's Steam library (a macOS copy of the Steam install).
2. Read the Steam app manifest for app 489830 in that library: `buildid` and `TargetBuildID`
   are both 24914197, so Steam records no pending update.
3. Read the executable's VERSIONINFO resource: FileVersion and ProductVersion are both `1.7.104.0`.
4. Ran `tools/fingerprint.py` (checks PE magic and AMD64 machine type, then SHA-256 of the whole file).

## Observations

- PE32+, machine AMD64, preferred image base `0x140000000`.
- Optional header linker version 14.16.
- An extra `.bind` section holds the entry point; this is Steam's executable wrapper.
- The main `.text` section's byte entropy is 5.7–6.5 bits/byte in every 1 MiB chunk, none near 8.

## Interpretation and alternatives

- Version `1.7.104.0` comes from the file itself, not from a toolkit archive name or a guess.
  The Steam build id ties it to the depot state Steam installed.
- Linker 14.16 corresponds to the Visual Studio 2017 15.9 toolset. This is a **hint** for
  compiler candidates in step 3, not evidence of the compiler that produced every object;
  objects compiled by an older compiler can be linked by a newer linker.
- The entropy figures are consistent with unencrypted code under the wrapper. They do not show
  that code regions are analyzable; step 2 must establish that in Ghidra.

## Reproduction and sanitized evidence

```sh
python3 tools/fingerprint.py '/path/to/Skyrim Special Edition/SkyrimSE.exe' \
  --store 'Steam (app 489830, Steam build 24914197)' --version '1.7.104.0'
```

The output's `image_sha256` must equal the value above. The private candidate is
`.local/target-candidate.json`. No bytes, disassembly or exports are published.

## Negative results and limitations

- The hash covers the file as installed, wrapper included. An analysis input that differs from
  this file needs its own reviewed identity; addresses must not be transferred without proof.
- Steam's build id identifies a depot state, not the executable alone; another file version
  under the same Steam build has not been observed and is not ruled out.
- The installation was copied to macOS; it was not launched to confirm the in-game version string.

## Reviewer and outcome

Pending maintainer review.
