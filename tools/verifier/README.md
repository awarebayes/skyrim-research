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
tools/verifier/session up | status | extend | down     # verifier session: machines A and B (Engineers/orchestrator)
tools/verifier/attempt .local/tasks/<task-id>          # one attempt: compile the unit, compare each function
tools/verifier/attempt --clean .local/tasks/<task-id>  # remove the task's files on the machine
tools/verifier/confirm .local/tasks/<task-id>          # acceptance evidence: A and B compile, 3 compare hosts, records
tools/verifier/confirm --session <task-dir>... [--out DIR] # many units on A then B, no starts, one table
tools/verifier/confirm --fork .local/tasks/<task-id>   # old path: one fork (one start) per unit
```

## Runners: where attempts and confirms run

`.local/verifier/runners.json` (private; example `runners.example.json`, parser `runners.py`)
names the hosts. Backends: `boat` (the session machines below, unchanged), `local` (this Mac:
the pinned compiler under Wine from `.local/toolchains/`, no network) and `ssh` (a host reached
with its own ssh_config; first use the maintainer's Windows PC, the pinned compiler run natively).
`"attempt"` picks the host `attempt` uses; `"confirm"` lists the compile hosts of a runner confirm
(two machines, two loaders). Without the file, attempt and confirm use Boat as before.

A local or ssh run uploads one archive (the unit's include closure, the comparator and host
scripts, the spec) and `host_agent.py`; the command line holds only paths and fixed options. The
host compiles and compares with `unit_build.py` (`--loader wine|native`), packs its work directory
for one fetch and deletes the run. `result.json` carries the host's OS, loader and the hashes of
the compiler binaries it ran. Each host has `max_parallel` slots (file locks under
`.local/verifier/runner-slots/`); attempts beyond that wait in turn.

```sh
python3 tools/verifier/runners.py status                    # each host: toolchain, image, CPUs, busy slots
python3 tools/verifier/reproduce_records.py --host <name>   # recompile every recorded unit there; equal/different
```

A runner confirm writes records only with `--out` until `docs/verification.md` admits these
hosts (`confirm_runners.RUNNER_RECORDS_ALLOWED`); `confirm --boat` keeps the Boat session path.

A session (`session`, `vsession.py`) brings up the standing machine A and the separately
installed B once per work period, at most one start each, and checks their toolchain and image
hashes; `attempt` and `confirm` then never start or stop a machine (`confirm_session.py`). Every
start by any tool goes through `starts.py` (budget from `boat limits`, a daily reserve, a log in
`.local/verifier/starts.jsonl`). Rules: `docs/boat-agent-guidelines.md`.

`<task-id>/task.json` (private) names the build id, compiled file, recipe, symbol map and the
functions (RVA, size, symbol); the format is in `pipeline.py`. Sources come from the checkout the
command runs in. `attempt` resumes or reuses the standing machine (extending its deadline when
under 15 minutes remain), uploads only changed files, and fetches reports, the object, the
compile log and private diagnostics to `<task-id>/attempts/<NNN>/`, with a local side-by-side
disassembly per function (`llvm-objdump`; G2 material, never printed; rows that differ only in
relocated fields are not marked). It binds unbound or renamed symbols from the compiled object
itself (`bind.py`, hints in `<task-id>/bind-hints.json`) and compares again in the same run; a run
that compared nothing because of binding is not counted against `max_attempts`, nor are a unit's
first three compile failures; a repository include the compiler would not find with the recipe's
include roots is refused locally before upload, also uncounted. `confirm` runs on the
working tree (records bind the unit digest, recipe and map hashes and, per report, the comparator
source hash, not a commit; a note in each record names the base commit, the comparator source hash
and every uncommitted input among the unit, recipe, map, comparator and verifier files), needs
inventory entries and the
repository symbol map, and refuses to overwrite a record without `--replace`. Both keep the target image on each machine at `~/private/<build id>/`
(uploaded once, checked by hash once per boot) and print only sanitized lines through
`boat exec`. Private settings live in `.local/verifier/config.json`:
`{"image": "<local SkyrimSE.exe>", "objdump": "<llvm-objdump>"}`.

## Files

- `runners.py`, `host_agent.py`, `confirm_runners.py`, `reproduce_records.py`, `runners.example.json`:
  runner selection and the local/ssh backends, the host-side script shipped with every run,
  confirm on runner hosts, and the reproduction of committed records on one host (tests in
  `tests/test_runners.py` use a stub ssh transport and a fake compiler).
- `session`, `vsession.py`, `confirm_session.py`, `starts.py`: verifier sessions, session-mode
  confirm and the starts budget (tests in `tests/test_session.py` use a fake `boat` CLI).
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
- `permute.py`: source permuter for one near-miss function, no model in the loop
  ([docs/permuter.md](../../docs/permuter.md)). Seeded rewrites of one body from the cookbook's
  mechanisable rules, every candidate linted, batches compiled in parallel on the standing
  machine in one `boat exec` each and scored with `align.py`; a distance-0 winner is compiled
  and compared once more by `unit_build.py`.
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
- `build_tls.sh <msvc-dir> <new-output-dir>`: compiles `synthetic/tls_cases.cpp` (linked into
  `tls.dll` with a map) and the perturbed `synthetic/tls_variant.cpp` (compiled only).
- `tls_compare.py <build-dir>`: the comparator's thread-local rules on that build: every `tls_`
  function passes with a map whose TLS-template names are `thread-local` entries; the variant
  object and altered maps or images fail. Metadata output only.
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
