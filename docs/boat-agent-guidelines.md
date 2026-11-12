# Boat guidelines for agents

Rules for every agent that uses a Boat machine. Background: [boat-build-worker.md](boat-build-worker.md),
[findings/boat-pilot.md](../findings/boat-pilot.md), [tools/verifier/](../tools/verifier/README.md).
Measured with Boat CLI 1.0.97 during the free trial. *(docs)* marks statements taken from
docs.boat.dev and not measured here. Limits change: `boat limits --json` is the truth.

## Sessions, not per-unit machines

Boat limits machine **starts**, not just compute. Work therefore runs in a **verifier session**:
two long-lived machines brought up once per work period and reused by every attempt and confirm.

- **A** = `sr-verifier-msvc141`, the standing verifier. **B** = `sr-verifier-b`, a second verifier
  built from scratch with the same recipe (`setup_boat_machine.sh`), not a fork. A pair of runs on
  A and B is labelled `independence: separate-machine` (`docs/verification.md`). Scripts find both
  by name (`boat list --all`); no machine id belongs in the repository.
- **One session per work period.** `tools/verifier/session up` at the start, `session down` at
  the end. While it is up, `attempt` uses A and `confirm` compiles on A and B; neither starts,
  stops or forks a machine. Without a session `attempt` may still resume A (one start), and
  `confirm` refuses unless given `--fork`.

## Who may start and stop machines

| role | may |
|---|---|
| Maintainer | everything below, plus billing and plan decisions |
| An Engineer whose orchestrator brief says so, or the `boat-up` / `boat-down` skills run for the maintainer or orchestrator | `session up/extend/down`, `confirm`, `confirm --fork` for a listed reason |
| Other Engineers | `attempt`, `confirm` and `session status` inside a session someone else owns |
| Drafters | `attempt` only. Never start, stop, fork, extend or create a machine ([drafter-card.md](drafter-card.md)) |

Nobody else starts a machine, and nobody calls `boat new`, `resume` or `fork` by hand when a
script does the job. Rules for those who may:

1. **Never fork per unit.** One session serves every attempt and confirm of the work period;
   `confirm --session <dir>...` confirms a whole batch on A and B with no start at all.
2. **Check `boat list --all` before creating anything.** `session up` does it and reuses a
   running machine or resumes a stopped one; a second machine with the same name is an error.
   Create only when the machine is missing (`session up --only b --create`).
3. **Stop when idle.** End the session when its work ends (`session down`); the auto-stop
   deadline is the backstop. A is shared: while other agents use it, end your session with
   `session down --keep a`, which stops B and leaves A running on its own deadline (its time is
   then booked by those agents' attempts, not as session overhead).
4. **Never stop a machine another agent is using.** `session down` refuses while a
   `~/tasks/<id>/.running` marker exists on a machine it would stop; `--force` is only for
   markers you know are stale.

`attempt --stop` is retired; per-task cleanup is `attempt --clean <task-dir>`.

## Starts budget

A start is a create (`boat new`), a fork or a resume *(docs)*. Measured: a `boat resume` moved
the day and hour `used` counters of `boat limits --json` up by one; `boat extend`, `boat exec`
and `boat stop` moved neither. Windows are rolling 60 s, 60 min and 24 h; there is no daily
reset *(docs)*. The old `confirm`, one fork per unit, used up the trial's daily starts in one
batch day; that is why sessions exist.

| plan | at once | starts per minute / hour / day | included VM time |
|---|---|---|---|
| trial (current) | 2 | 5 / 25 / 75 | 25 h in total |
| $20 paid plan *(docs)* | 100 | 12 / 60 / 200 | 555 h per month of `default` |

Check before and after any start: `python3 tools/verifier/starts.py status` (one line) or
`session status`. Every tool that can start a machine (`session`, `attempt` without a session,
`confirm --fork`, `boat_up.sh`) goes through `tools/verifier/starts.py`: it reads `boat limits`,
logs the start and its reason to `.local/verifier/starts.jsonl`, and refuses a start that would
leave fewer than the reserve for the rest of the day (default 10, `SR_STARTS_RESERVE`; `--force`
or `SR_STARTS_FORCE=1` uses the reserve). A full minute or hour window is always refused: wait.
A session costs at most one start per machine; a day of work is about 2 to 4 starts.

## When forking is still right

- An isolated, risky experiment that must not touch A or B (new compiler flags in setup, a
  toolchain probe): fork the **stopped** A with `--no-env --ttl <s> --wait`, name it
  `sr-<task-id>`, stop and `boat delete --yes` it at the end. A fork of a running machine uses a
  snapshot up to a minute old.
- A fan-out (the permuter, a later fleet) starts each machine **once** and reuses it for the
  whole run, like a session; never one machine per candidate or per unit.
- `confirm --fork` only when the brief names the reason (B unavailable, a fork-labelled check).
  It costs one start per unit and the record says `independence: fork`.
- On the trial at most 2 machines run at once: with A and B up no fork can start.

## Idle cost and deadlines

A running machine bills second for second whether it works or not; nothing is billed while
stopped *(docs)*. Two `default` machines for an 8-hour session are 16 machine-hours against 555
included per month on the $20 plan ($0.036/h each *(docs)*). So:

- Every machine has an auto-stop deadline. It counts from creation or the last resume or extend,
  not from activity; `boat exec` does not extend it (measured). Trial maximum 7200 s.
- `session up --ttl S` sets it on resume; on a machine that is already running it never moves a
  deadline earlier. `session extend --ttl S` pushes running session machines to now + S when
  work goes on; `attempt` and `confirm` extend by themselves when under 15 minutes remain.
  Extending is not a start (measured).
- End the session when the work ends; auto-stop is the backstop, not the plan.

## Retention

A stopped disk is kept at least 14 days after a stop *(docs)*; each resume restarts the clock.
`session status` warns when a machine has been stopped 10 days or more: then run
`session up --only <a|b>` and `session down --only <a|b>` (one start, a few billed seconds).
Saved snapshots are refused on the trial (`403 trial_saved_snapshots_not_allowed`); after the
first payment the maintainer, not an agent, decides to save `sr-verifier-msvc141-v<N>`.
If A or B is gone (`409 snapshot_data_expired` or missing): B is rebuilt with
`session up --only b --create`; A with `BOAT_ALLOW_CREATE=1 tools/verifier/boat_up.sh`. Both
run the full recipe and accept the Build Tools licence: G3 and G4 needed, the maintainer told first.

## Commands

```sh
python3 tools/verifier/starts.py status              # starts budget, one line
tools/verifier/session up [--ttl 3600] [--only b] [--create]   # resume/reuse A and B, verify hashes
tools/verifier/session status                        # state, deadlines, task markers, starts, compute
tools/verifier/session extend --ttl 3600             # push deadlines while work goes on
tools/verifier/session down [--only b] [--keep a] [--force]   # refuses with active markers; stops; queues cost
python3 tools/cost_ledger.py flush                   # move queued compute into data/costs.json
tools/verifier/attempt <task-dir>                    # on A; no start inside a session
tools/verifier/confirm <task-dir> | --session <dir>... | --list <file> [--out <dir>]   # --all = --session
```

The skills `boat-up`, `boat-status` and `boat-down` (`.claude/skills/`) run these for the
maintainer or the orchestrator. `session up` checks each machine's compiler binaries against
`pinned.sha256` and its image at `~/private/<build id>/SkyrimSE.exe` against
`builds/target.json` (uploading it to B once); a failed check leaves the machine unverified and
unused. `boat_up.sh`, `boat_run.sh` and `boat_down.sh` remain for single-machine tasks
(`boat_run.sh <task-id> <local-dir> '<command>'` runs in `~/tasks/<task-id>`).
Direct CLI use: prefer `boat exec <id> --timeout N -- '<cmd>'` over `boat ssh`; default exec
timeout is 30 s (exit 143, `timedOut: true`).

## Sharing a machine

- One task = one directory `~/tasks/<task-id>` (confirm uses `~/tasks/<task-id>-confirm`).
  Never write into another task's directory, `~/msvc`, `~/private` or `~/sr`.
- `boat push` does not delete remote files removed locally; do not rely on a file's absence.
- No installs (apt, `setup_boat_machine.sh`, changes under `~/msvc`) on a machine in a session.
- `confirm --session` runs units in parallel up to the machines' CPU count (4 on `default`).

## What may go on a machine

| input | needs |
|---|---|
| original/synthetic code, repository `tools/` | G3 |
| licensed Microsoft toolchain/SDK (via the recipe only) | G3 + G4 |
| target executable (in `~/private/<build id>/` only), slices, reconstructed source | G3 + G5 |
| reading game-derived output back into a model | G2 |

Never: credentials of any kind (SSH keys, git tokens, Boat API keys, `.env` files, model keys),
files outside this repository's allowed inputs, or untrusted PR/third-party code. Always
`--no-env` on `new` and `fork`; never `boat share`, `host`, `desktop`, `prompt` or `ai`. Boat
keeps `exec` output for 90 days *(docs)*: print only sanitized summaries (counts, hashes, pass/fail).

## Buy nothing

Agents never run `boat billing ...` (plan, portal, `extra-starts`, purchases), wallet top-ups,
open dashboard billing links, end the trial, save snapshots beyond the included count, or use
`large`/`xlarge`. If a limit blocks the work (`429 rate_limited`, `limit_reached`,
`trial_compute_limit_reached`, `402 billing_required`, or the starts reserve), stop and report.

## End-of-session checklist (results go in the handoff)

1. `session status`: no task markers left that are yours; note starts used and compute.
2. `session down` (`--keep a` while others use A); every machine you stopped is `stopped` in `boat list --all`.
3. `python3 tools/cost_ledger.py flush`; the session's overhead seconds and start count are in it.
4. Forks you made: stopped and deleted. No billing command ran; wallet unchanged.
5. Results fetched to `.local/`; `~/tasks/<task-id>` removed (`attempt --clean`, confirm cleans
   itself). The target image in `~/private/<build id>/` stays: the maintainer allows it there.

## Measured cost and time (`default` type)

| step | wall time | notes |
|---|---|---|
| fresh machine + `setup_boat_machine.sh` | 93 s to 7 min; 209 to 404 s billed | apt, 748 MB download, unpack |
| `boat resume` to ready, cold | 4.7 s | first reads of compiler files 14 s, then 4 s |
| `boat fork` of a stopped machine to ready | 4.2 s | whole fork with one build 23 s billed |
| `boat stop` returns / reaches `stopped` | 0.3 s / 5.1 s | |
| `boat exec <id> true`; `scp` 100 KB | 1.1 s; 1.7 to 1.9 s | `boat ssh` first use 22.7 s |
| `session up` with A running, B stopped | about 40 s | 1 start; resume of B plus hash checks on both |
| `confirm --session` of 2 one-function units | 6 s | 0 starts; 4 runs per function, all on A, B and this Mac |
| `session down --keep a` | about 5 s | stops B; B billed 23 s for the whole session |

## Troubleshooting

| symptom | cause and fix |
|---|---|
| `starts: not starting ...` | reserve or window full: wait, or the owner passes `--force` within the reserve |
| attempt: `session is up but ... is stopped` | auto-stop ended the session machine; tell the session owner |
| `scp -r` upload fails, `._*` files remote | macOS tar AppleDouble files; `COPYFILE_DISABLE=1` (scripts set it) |
| `boat push` reports `"files":0` | push skips gitignored paths; use `scp -r` for `.local/` |
| exec `timedOut: true`, exit 143 | default 30 s exec timeout; pass `--timeout` |
| `409 sandbox_not_ready` | machine stopped; the session owner runs `session up` |
| `400 trial_auto_stop_required` | TTL above 7200 or no auto-stop on trial |
| toolchain or image check fails | do not verify on that machine; report it, never reinstall silently |
| `more than one sandbox is named ...` | rename the extra one; scripts never guess |
| comparator `invalid-task` | task ids must not contain underscores |

Sources: [Limits](https://docs.boat.dev/limits), [Pricing](https://docs.boat.dev/pricing),
[Free trial](https://docs.boat.dev/free-trial), [Resume and fork](https://docs.boat.dev/snapshots/resume-and-fork),
[Stop](https://docs.boat.dev/snapshots/stop), [Auto-stop](https://docs.boat.dev/long-running-tasks/auto-stop),
[Data retention](https://docs.boat.dev/data-retention), [Security](https://docs.boat.dev/security);
`boat <command> --help` (CLI 1.0.97).
