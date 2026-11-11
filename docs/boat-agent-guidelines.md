# Boat guidelines for agents

Rules for every agent that uses a Boat machine. Background: [boat-build-worker.md](boat-build-worker.md),
[findings/boat-pilot.md](../findings/boat-pilot.md), [tools/verifier/](../tools/verifier/README.md).
Measured with Boat CLI 1.0.97 on 2026-11-11 (UTC) during the free trial. *(docs)* marks statements
taken from the docs and not measured here. Limits change: `boat limits --json` is the truth.

## Lifecycle rules

1. **Resume, never rebuild.** The standing verifier machine is named `sr-verifier-msvc141`
   (look it up with `boat list --all`; scripts find it by name). It holds the pinned toolchain.
   Bring it up with `tools/verifier/boat_up.sh` (resume plus hash check), never with `boat new`.
2. **Parallel or risky work: fork the stopped machine**, do not create one. `boat fork <id>
   --no-env --ttl <s> --wait` works on the trial and gives a full copy (measured). Fork only
   while the source is stopped: a fork of a running machine uses a snapshot up to a minute old.
   Name it `sr-<task-id>`, stop it at the end, then `boat delete --yes` it (forks are disposable;
   only the standing machine is kept).
3. **Create from scratch only if the standing machine is gone** (`409 snapshot_data_expired` or
   missing): `BOAT_ALLOW_CREATE=1 tools/verifier/boat_up.sh`. That runs the full recipe and accepts
   the Build Tools licence; it needs G3 and G4 and the maintainer told first.
4. **Stop, don't delete, the standing machine.** A stop snapshots the disk; stopped machines are not
   billed. The disk is kept at least 14 days after a stop, and each resume restarts that clock
   *(docs)*. If it will sit unused for more than 12 days, tell the maintainer so it gets a
   resume/stop cycle (about 4 s billed) or, once paid, a saved snapshot.
5. **Snapshots:** saved snapshots are refused on the trial (`403 trial_saved_snapshots_not_allowed`,
   measured). After the first payment the $20 plan includes 10 *(docs)*; the maintainer, not an
   agent, decides to save `sr-verifier-msvc141-v<N>` and then fleets use `boat new --from <name>`.
6. **Always set a deadline.** Auto-stop counts from creation or the last resume, not from activity;
   `boat exec` does not extend it, and idle running time is billed per second (85 s billed over
   85 s idle, measured). Trial maximum is 7200 s. `boat resume --ttl N` also stores N as the
   machine's TTL for later resumes (measured). For a long job run `boat extend <id> --ttl N` first;
   it sets the deadline to now + N *(docs)*.
7. **One standing machine per toolchain.** Never install a second toolset on it; a different
   compiler gets its own machine and recipe.

## Commands

```sh
export BOAT_CLI=boat              # or the CLI path on this host; scripts also set BOAT_NO_UPDATE=1
boat limits --json                # record trialComputeUsedSeconds / creditUsedSeconds first
tools/verifier/boat_up.sh         # resume (or reuse) + push tools/ + check pinned.sha256
tools/verifier/boat_run.sh <task-id> <local-dir> '<command>'   # runs in ~/tasks/<task-id>
tools/verifier/boat_down.sh       # refuses while tasks are marked running; stops; prints compute
```

`boat_run.sh` uploads `<local-dir>` to `~/tasks/<task-id>/in`, empties `out/`, runs the command
under bash with `IN`, `OUT`, `SR` (`~/sr`, repository tools) and `MSVC` (`~/msvc`) set, copies
`out/` back to `.local/boat-results/<task-id>/` and exits with the command's code (124 on
timeout; `BOAT_RUN_TIMEOUT` seconds, default 600, 0 for none). Direct CLI use: prefer
`boat exec <id> --timeout N -- '<cmd>'` over `boat ssh`; output is JSON when not on a terminal
and the exit code is the command's (measured). Default exec timeout is 30 s; up to 600 s runs
synchronously, longer or 0 streams *(docs; 3 s timeout measured: exit 143, `timedOut: true`)*.

## Cost and time (measured, `default` type)

| step | wall time | notes |
|---|---|---|
| fresh machine + `setup_boat_machine.sh` (pilot) | about 7 min; 404 s billed | apt, 748 MB download, unpack |
| fresh machine + `setup_boat_machine.sh` (second host) | 93 s setup; 209 s billed for the machine's whole life including one task | hashes matched `pinned.sha256` |
| `boat resume` to ready, cold (more than 10 min after stop) | 4.7 s | new machine, disk intact, hashes OK |
| first reads after cold resume (hash 4 compiler files) | 14.3 s, then 4.3 s warm | files download lazily on first read; `build_pilot.sh` then 19.6 s |
| `boat_up.sh` within 10 min of a stop | 4 s total | same machine taken back, no restore |
| `boat fork` of the stopped machine to ready | 4.2 s | hash check + pilot build 6 s; whole fork 23 s billed |
| `boat stop` returns / reaches `stopped` | 0.3 s / 5.1 s | |
| `boat exec <id> true`; `boat push` / `scp -r` down, 100 KB | 1.1 s; 1.9 s / 1.7 s | `boat ssh <id> true`: 22.7 s first (key setup), 5.2 s after |
| scripted cold cycle: `boat_up` 7 s, `boat_run` compile 4 s, `boat_run` pilot build 7 s, `boat_down` 10 s | 28 s total; 17 s billed | 14 min after the previous stop |
| first manual experiment cycle (resume, checks, transfers, build, stop) | 217 s billed | about 3.6 min running |

Billing: per second while starting or running; nothing while stopping or stopped *(docs)*.
`default` is $0.036/h from plan time *(docs)*; the trial has 25 compute hours in total, 2
machines at once and 5/25/75 starts per minute/hour/day, and resume, fork and create each count
as a start *(docs; `boat limits` agrees)*. Record compute before and after every task.

## Sharing one machine between agents

- One task = one directory `~/tasks/<task-id>` (`boat_run.sh` enforces this). Never write into
  another task's directory, `~/msvc` or `~/sr` except through `boat_up.sh`.
- `boat_up.sh` pushes this checkout's `tools/`; `boat push` does not delete remote files removed
  locally (measured), so do not rely on absence of a file in `~/sr/tools`.
- No parallel installs: apt, `setup_boat_machine.sh` or any change under `~/msvc` runs only when
  the orchestrator has given one agent the machine exclusively.
- `boat_run.sh` writes `~/tasks/<task-id>/.running` while a command runs; `boat_down.sh` refuses
  to stop while any exists. Only the agent that owns a stale marker (left by a timeout) removes it
  or uses `--force`. Auto-stop is the backstop, not the plan.
- At most 2 machines at once on the trial: the standing machine plus one fork, and only when the
  orchestrator's brief allows it.

## What may go on a machine

| input | needs |
|---|---|
| original/synthetic code, repository `tools/` | G3 |
| licensed Microsoft toolchain/SDK (via the recipe only) | G3 + G4 |
| target executable, slices, reconstructed source | G3 + G5, and the task brief must name it |
| reading game-derived output back into a model | G2 |

Never: credentials of any kind (SSH keys, git/GitHub tokens, Boat API keys, `.env` files, model
keys), files from outside this repository's allowed inputs, or untrusted PR/third-party code (the
machine holds licensed tools and possibly game data). Always `--no-env` on `new` and `fork`; never
`boat share`, `boat host`, `boat desktop`, `boat prompt` or `boat ai`. Boat keeps `exec` output
for 90 days *(docs)*: write bulky or game-derived output to files under `out/` and print only
sanitized summaries (counts, hashes, pass/fail).

## Buy nothing

Agents never run `boat billing ...` (plan, portal, extra-starts, purchases), `boat wallet`
top-ups, open dashboard billing links, end the trial, save snapshots beyond the included count,
or use `large`/`xlarge`. If a limit blocks the task (`429 limit_reached`, `rate_limited`,
`trial_compute_limit_reached`, `402 billing_required`), stop and report to the maintainer.

## End-of-task checklist (put the results in the handoff)

1. `boat limits --json` before (already recorded at start) and after: `trialComputeUsedSeconds`
   (or `creditUsedSeconds` after the trial).
2. Every machine you started or resumed is `stopped` (`boat list --all`); forks also deleted.
3. `boat usage <id> --json` seconds for each machine touched.
4. No billing command ran; wallet unchanged.
5. Results fetched to `.local/`; nothing game-derived left in `~/tasks/<task-id>` unless the brief
   says to keep it (`rm -rf ~/tasks/<task-id>` before stopping otherwise).

## Troubleshooting

| symptom | cause and fix |
|---|---|
| `boat scp -r` upload: `archive upload failed (tar ..., ssh: exit status: 1)`, `._*` files remote | macOS tar adds AppleDouble files. Set `COPYFILE_DISABLE=1` (measured fix) |
| `boat push` reports `"files":0` | push skips gitignored paths, so nothing under `.local/` is copied. Use `scp -r` |
| `tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr...'` | harmless warning on upload |
| exec returns `timedOut: true`, exit 143 | default 30 s exec timeout; pass `--timeout` |
| `403 trial_saved_snapshots_not_allowed` | trial; fork the stopped machine instead |
| `409 sandbox_not_ready` | machine stopped; run `boat_up.sh` |
| `409 snapshot_data_expired` | disk retention ended; rebuild (lifecycle rule 3) *(docs)* |
| `400 trial_auto_stop_required` | TTL above 7200 or `--no-auto-stop` on trial |
| `sha256sum -c` FAILED in `boat_up.sh` | do not verify on that machine; report it, do not reinstall silently |
| `boat_up.sh` create path exits 141 and leaves a machine | SIGPIPE from the ready-line parser under `pipefail` (fixed). Earlier copies: finish by hand with `boat push` of `tools/`, then `setup_boat_machine.sh`, then `sha256sum -c` |
| first `boat push` right after create fails | seen once on a new machine; it succeeded when repeated |
| `setup_boat_machine.sh` exits 3 | `pinned.sha256` missing next to it (pilot run 1) |
| comparator `invalid-task` | task ids must not contain underscores (pilot) |
| comparator import error under `python3 -I` | run `tools/compare.py` without `-I` so it finds `pecoff.py` (pilot) |
| first `boat ssh` takes 20+ s | one-time key setup; use `boat exec` instead |
| `more than one sandbox is named ...` from the scripts | rename the extra one; scripts never guess |

## Sources (accessed 2026-11-11)

[Free trial](https://docs.boat.dev/free-trial), [Resume, fork and restore](https://docs.boat.dev/snapshots/resume-and-fork),
[Saved snapshots](https://docs.boat.dev/snapshots/templates), [Stop](https://docs.boat.dev/snapshots/stop),
[Readiness](https://docs.boat.dev/readiness), [Auto-stop](https://docs.boat.dev/long-running-tasks/auto-stop),
[Background commands](https://docs.boat.dev/long-running-tasks/background-commands),
[Pricing](https://docs.boat.dev/pricing), [Limits and errors](https://docs.boat.dev/limits),
[Security](https://docs.boat.dev/security), [Data retention](https://docs.boat.dev/data-retention),
[SSH](https://docs.boat.dev/ssh-access), [Windows apps: agents and forks](https://docs.boat.dev/windows-apps/agents-and-forks),
[What a snapshot saves](https://docs.boat.dev/snapshots/whats-saved); `boat <command> --help` (CLI 1.0.97).
Docs vs observed: no contradiction found. The docs' Wine example (16 GB) reports 20 to 32 s
resumes; this machine (about 3 GB of tools in home) was ready in under 5 s, first reads slower.
