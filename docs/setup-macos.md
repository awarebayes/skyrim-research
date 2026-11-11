# macOS and Windows setup

## Bootstrap environment

The initial checkout was prepared on Apple Silicon macOS. Git and Python 3.11+ are enough
for repository validation and generating the static report. No VM, Ghidra, compiler or game
has been installed or configured by the bootstrap. Check available disk before provisioning:
the bootstrap machine had only about 17 GiB free. Do not delete Mudcrab worktrees or assets.

```sh
python3 tools/check.py
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
```

## Local input preparation

Keep the legally obtained game outside the repo. Record hashes without printing its contents:

```sh
mkdir -p .local
python3 tools/fingerprint.py '/path/to/your/SkyrimSE.exe' --store 'your store' --version 'actual version' > .local/target-candidate.json
```

This only reads the file, verifies the PE machine type and computes SHA-256. It does not
unpack, execute, patch or upload it, and does not prove the code is suitable for analysis.
Review the candidate, add an accurate build id and scope notes, then update `builds/target.json`
and the matching `data/progress.json` target id in a separate reviewed change. A version string
is a contributor assertion: this tool does not extract or authenticate the release version.
Do not infer the target from a toolkit release filename. No game bytes go into the manifest.

## Static analysis

Use Ghidra and the Skyrim RE Toolkit's prebuilt `.gdt` archives as a starting point, with the
runtime variant and dependency revisions recorded. Check current upstream Ghidra/JDK macOS
requirements; this project's Apple Silicon import path has not been reproduced yet. Native
components or Linux-oriented scripts may need adaptation. Store the Ghidra project and exports
under `.local/analysis/`. Initial import, addresses and type application must be validated before
using them as evidence. See the pinned toolkit reference in `SOURCES.md`.

## Compiler worker

An Apple Silicon VM generally runs Windows 11 Arm, with x86/x64 user-mode application emulation.
Parallels is one option. This project's legacy compiler compatibility has NOT been tested there.
Select a Skyrim-specific toolchain experimentally; do not assume FNV's VC2008 toolchain applies.
Pin compiler hashes, host/target architecture, SDK and flags before claiming reproducibility.
Use `.local/compilers/` or an external private VM volume, never commit installer packages.

First prove an ordinary synthetic C++ compile, then the comparison path, then a small actual
function. Do not provision paid services or install large VM images merely to run repo checks.

## Runtime experiments

Skyrim launch, SKSE loading, plugin hooks and debugger attachment in a Windows Arm VM are
separate unverified milestones. Do not claim vanilla x64 Windows compatibility results apply
to this VM. If needed, use a separately authorized x64 Windows host for runtime measurements.
Use isolated test saves and read-only original inputs; never overwrite the user's installed exe.

References: [Windows Arm emulation](https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation),
[Parallels](https://www.parallels.com/products/desktop/),
[toolkit demo](https://github.com/ByteBard97/skyrim-re-toolkit/tree/master/demo),
[FNV compiler workflow](https://github.com/momusdigital/fnv_decomp#what-you-need).
