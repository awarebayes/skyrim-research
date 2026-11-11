# Verifier worker recipe (pilot)

Reproduces the compiler worker described in `findings/boat-pilot.md`: MSVC v141
(Visual Studio 2017 15.9 Build Tools, x64 host and target) under Wine on a fresh x86-64
Ubuntu 24.04 machine, then builds and compares original synthetic code. Nothing here touches
game data; the comparator is exercised only on the synthetic pilot sources.

This establishes a build worker. It does not establish that this is the compiler the target
was built with, and no step compares anything against the game.

## Files

- `setup_boat_machine.sh`: installs Wine and msitools from the Ubuntu archive, checks out
  msvc-wine at a pinned commit, downloads a pinned Visual Studio installer manifest (checked by
  SHA-256), downloads and unpacks the toolset and Windows SDK from Microsoft's servers, then
  checks the compiler binaries against `pinned.sha256`. Running it accepts the Microsoft Build
  Tools licence (`--accept-license`); only run it where that licence basis is recorded.
- `pinned.sha256`: expected SHA-256 of `cl.exe`, `c1xx.dll`, `c2.dll` and `link.exe`.
- `build_pilot.sh <msvc-dir> <new-output-dir>`: compiles `synthetic/pilot.cpp` and
  `synthetic/pilot_variant.cpp` and links `pilot.dll` with a map file. Run it twice.
- `pilot_compare.py determinism A B`: attributes every differing byte between two builds to a
  named field; prints hashes and counts only.
- `pilot_compare.py compare A B --work .local/... --recipe recipe.json`: runs
  `tools/compare.py` on object A against image B for each pilot function, plus negative cases.
  The work directory must be under `.local/` because the comparator writes diagnostics there.
- `synthetic/`: original test sources. No third-party code.

## Steps

From a checkout (or a copy of `tools/compare.py`, `tools/pecoff.py` and `tools/verifier/`) on
the worker machine. Copy no credentials and no game-derived files to it.

```sh
tools/verifier/setup_boat_machine.sh "$HOME/msvc"
tools/verifier/build_pilot.sh "$HOME/msvc" .local/pilot/a
tools/verifier/build_pilot.sh "$HOME/msvc" .local/pilot/b
python3 -I tools/verifier/pilot_compare.py determinism .local/pilot/a .local/pilot/b
python3 -I tools/verifier/pilot_compare.py compare .local/pilot/a .local/pilot/b \
  --work .local/pilot/compare --recipe .local/pilot/recipe.json
```

`recipe.json` names the compiler hash and version and the flags from `build_pilot.sh`; its
format is the one `docs/comparator-contract.md` describes.

## Known limits of the recipe

- The installer manifest is pinned by URL. If Microsoft withdraws that URL, the recipe stops
  at the manifest hash check; it never silently follows the channel to a newer release.
- Package payloads are verified against the manifest by `vsdownload.py`; the toolset binaries
  are then checked against `pinned.sha256`. The SDK files are not individually pinned.
- Boat machines are shared-vCPU VMs; timing is not representative. Wine is the Ubuntu 24.04
  package, not a pinned upstream build; its version is printed by the setup script.
