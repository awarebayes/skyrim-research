# Verifier worker recipe and scripts

Reproduces the compiler worker described in `findings/boat-pilot.md`: MSVC v141
(Visual Studio 2017 15.9 Build Tools, x64 host and target) under Wine on a fresh x86-64
Ubuntu 24.04 machine. The pilot scripts build and compare original synthetic code only.
`verify_function.py`, `tu_task.py` and `match_record.py` are the per-function path: they compare
a compiled reconstruction against the pinned image you supply (private, under the gates in
`AGENTS.md`) and assemble the sanitized match record. No script here contains game data.

The recipe establishes a build worker. It does not establish that this is the compiler the
target was built with.

## Per-function commands

```sh
tools/verifier/attempt .local/tasks/<task-id>          # one attempt: compile the unit, compare each function
tools/verifier/attempt --stop [.local/tasks/<task-id>] # Engineers only: stop the standing machine
tools/verifier/confirm .local/tasks/<task-id>          # acceptance evidence: fork, 2 compile hosts, 3 compare hosts, records
```

`<task-id>/task.json` (private) names the build id, compiled file, recipe, symbol map and the
functions (RVA, size, symbol); the format is in `pipeline.py`. Sources come from the checkout the
command runs in. `attempt` resumes or reuses the standing machine (extending its deadline when
under 15 minutes remain), uploads only changed files, and fetches reports, the object, the
compile log and private diagnostics to `<task-id>/attempts/<NNN>/`, with a local side-by-side
disassembly per function (`llvm-objdump`; G2 material, never printed; rows that differ only in
relocated fields are not marked). It binds unbound or renamed symbols from the compiled object
itself (`bind.py`, hints in `<task-id>/bind-hints.json`) and compares again in the same run; a run
that compared nothing because of binding is not counted against `max_attempts`. `confirm` runs on the
working tree (records bind the unit digest, recipe and map hashes and, per report, the comparator
source hash, not a commit; a note in each record names the base commit, the comparator source hash
and every uncommitted input among the unit, recipe, map, comparator and verifier files), needs
inventory entries and the
repository symbol map, and refuses to overwrite a record without `--replace`. Both keep the target image on each machine at `~/private/<build id>/`
(uploaded once, checked by hash once per boot) and print only sanitized lines through
`boat exec`. Private settings live in `.local/verifier/config.json`:
`{"image": "<local SkyrimSE.exe>", "objdump": "<llvm-objdump>"}`.

## Files

- `attempt`, `confirm`: the commands above; `pipeline.py` holds their shared logic, `boatctl.py`
  the Boat CLI calls, `disasm.py` the local side-by-side disassembly, `bind.py` the binding of
  decorated names to target RVAs (rules and hint format in its docstring).
- `align.py`: aligned diagnostics for a failing function. It normalises both listings (registers
  as widths, references as RVAs, branches as labels), aligns them, names each difference in a
  fixed vocabulary that maps onto `docs/matching-cookbook.md`, and gives one distance with
  prologue, body and reference components (formula in its docstring; 0 only for identical bytes).
  `attempt` prints its summary (no bytes, no instruction text) under each failing function and
  writes `align.txt` (private aligned listing) and `align.json` (for a search tool) next to the
  side-by-side. Run it on stored attempts with `tools/verifier/align.py --attempt <dir>`. A
  reading aid and a score, never evidence of a match.
- `unit_build.py`: runs on the verifier host. Checks the synced copy against the spec's hashes,
  the toolchain against `pinned.sha256` and the image against `builds/target.json` (once per
  boot), compiles with the build-path checks of `docs/verification.md` (cleared `INCLUDE`/`CL`/
  `_CL_`, `/showIncludes` equal to the include closure), then runs `verify_function.py` per
  function.
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
- `build_eh.sh <msvc-dir> <new-output-dir>`: compiles `synthetic/eh_cases.cpp` with the first
  recipe's flags and `synthetic/eh_gs.cpp` with `/GS` added, and links `eh.dll` with a map.
- `eh_compare.py <build-dir>`: comparator contract v2 on that build: every exported function
  compared object against DLL (try/catch, destructors, SEH, GS handlers, jump tables, chained
  unwind), then negative cases on altered copies of the image or map. Metadata output only.
- `eh_census.py <image> [--sample verdicts.tsv]`: walks every function's unwind chain and handler
  data in an image with the comparator's layouts and prints counts only: handlers by kind, how
  many decode completely, reasons for the rest, and with `--sample` the survey sample's supported
  share before and after contract v2.
- `synthetic/`: original test sources. No third-party code.
- `verify_function.py`: runs `tools/compare.py` for one candidate function from a task
  description file and prints a sanitized summary.
- `tu_task.py`: writes that task description and the build record for a compiled
  translation unit under `reconstruction/`. It takes identity from the inventory and
  `builds/target.json`, and the source revision from `tools/source_digest.py`.
- `match_record.py`: assembles a match record under `reports/` from comparator reports and refuses
  any record `tools/check.py` would reject (`reports/README.md`).
- `boat_up.sh`, `boat_run.sh`, `boat_down.sh` (with `boat_lib.sh`): resume the standing Boat
  verifier machine and check `pinned.sha256`, run one task in its own `~/tasks/<task-id>` with a
  file round trip, and stop it while printing compute used. Usage and rules are in
  `docs/boat-agent-guidelines.md`; `BOAT_CLI` overrides the CLI path.

After the comparison lines `attempt` prints the findings of `tools/check_labels.py` on the unit's
sources as `label warning:` lines (COMMUNITY names and enumerator values checked against the local
pinned community checkouts, GUESS names those checkouts declare, Evidence files that miss a compared
RVA). They never change the exit status; the check reads private clones and does not run in CI.

`attempt` and `confirm` queue their Boat usage for the cost ledger through `tools/cost_hooks.py`
when that module is present (wall time for an attempt, the compute counter delta for a confirm);
without it they skip the bookkeeping.

Related tools outside this directory:

- `tools/compare.py` (with `tools/pecoff.py`): the comparator, contract in
  `docs/comparator-contract.md`. Changing either file makes every match record stale.
- `tools/source_digest.py`: the `tu-sha256-v1` digest of a translation unit, used as the source
  revision by tasks, records and Reviewer records.
- `tools/check.py`: the validator, including the match gate (`docs/verification.md`).
- `tools/accept_function.py`: records a Reviewer `approve` and sets one inventory entry to
  `matched`, or revokes an acceptance (`--revoke`). It refuses anything the gate would reject.

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
