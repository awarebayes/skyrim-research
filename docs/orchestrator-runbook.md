# Orchestrator runbook (routine queue work, any model)

Paste into a fresh session started in this repository, naming the profile:
`Read docs/orchestrator-runbook.md in this repository and follow it exactly. Your profile is <cheap|full|claude-low>.`

You are the routine orchestrator. Goal: move functions through the pipeline (draft, confirm,
review, accept, push) by executing the list `python3 tools/flow.py next-actions` prints. The tool
holds the state and decides the order; you decide nothing about ordering and judge nothing about
matches. Planning, new kinds of work and every exception below belong to the planning
orchestrator (`.claude/agents/orchestrator.md`, strongest model) or the maintainer.

## Five binding rules

1. **Private stays private.** Everything under `.local/` is game-derived or private. Never paste
   it into a commit, an issue, a PR, a public message or a brief for a model whose exposure is
   not recorded in `docs/authorizations.md`.
2. **Only tools decide.** A match is a comparator report; acceptance is `tools/accept_function.py`
   run by `flow.py integrate`. Never claim a pass, an approval or a green CI a tool did not print.
3. **Never weaken a check.** Never edit the comparator, validator, lint, a match record, a saved
   review, `docs/verification.md`, `docs/authorizations.md`, `AGENTS.md` or agent definitions. A
   refusal is a stop, not a problem to work around.
4. **Workers get a brief path, not prose.** Every worker you start gets one line naming a brief
   file `flow.py` wrote. You never write briefs by hand.
5. **Small context.** Workers return a short table; full output is in files. Do not open a review,
   handoff or log unless a step below tells you to.

## Starting a worker

`next-actions` names the role, the model, the harness and the one-line prompt. Start it the way
your harness does:

| harness | how |
|---|---|
| Claude Code (Agent tool) | `Agent` with `subagent_type` as given (`reviewer`, `engineer`, `drafter`, `direction-check`), `model` as given, the prompt line as given. Independent starts go in one message so they run in parallel. Code-writing workers that may overlap get `isolation: "worktree"`. |
| T3 (`delegate_task`) | `delegate_task` with the model and effort given and the prompt line as the task text. |
| any other (two terminals) | open a second terminal in this repository, start the named model's CLI there (Claude Code, Codex) with the model and effort given, and paste the prompt line. Wait for its return table. |

**Reviewer model.** The acceptance rule (`docs/verification.md`, "Admitted Reviewer classes")
admits Sonnet Reviewers by default and Terra Reviewers under `claude-low`; `flow.py` gives sampling
second passes and confirmations of a non-Opus escalation to Opus by itself. A profile Reviewer the
rule does not admit is replaced by Opus with a note.

A Codex worker that should follow a runbook gets the runbook line: Reviewer
`Read docs/reviewer-runbook.md and follow it. Your brief is <brief path>.`; Drafter
`Read docs/drafter-runbook.md in this repository and follow it exactly. Your worker label is <label>.`

## The loop

1. `python3 tools/flow.py session-start --profile <profile>` (once per session). It prints which
   model does each role.
2. `python3 tools/flow.py next-actions`. It prints numbered lines, each `[stop]`, `[run]`,
   `[dispatch]`, `[wait]`, `[end]` or `[done]`.
3. Do every `[stop]` line first: report it (see "Stop and escalate"), and do nothing else for the
   group it names. Lines for other groups may continue.
4. Do the `[run]` and `[dispatch]` lines from the top, exactly as written:
   - `[run]`: run the command. If it prints a brief path and says to start a worker, start one
     worker per brief path ("Starting a worker").
   - `[dispatch]`: start the worker as written, then run the `Then:` command it gives (for example
     `python3 tools/flow.py dispatched g004`) so the tool knows.
   - A command that exits non-zero: read its last lines. If it says `STOPPED at`, `REFUSED`,
     `DISAGREE`, `ESCALATE`, or CI `RED`, that is a stop: go to "Stop and escalate". Otherwise run
     it once more; a second failure is a stop.
5. `[wait]` lines need no action: workers are running. When a worker returns its table, check
   that the file it names exists (`ls <path>`), then go back to step 2. Do not read the file.
6. When only `[wait]` and `[end]` lines remain and no worker is running, or after about four
   hours, do the `[end]` lines and finish ("End of session").

`flow.py integrate <group>` is the whole integration: it runs the strict review parser,
`tools/accept_function.py`, `tools/check.py --staged`, a commit, the pre-push checks in a clean
worktree (`check.py`, unit tests, `build_site.py`), the push and `tools/ci_status.py`. It stops at
the first failure and resumes after the last finished step when run again. It builds the commit
in its own worktree at `origin/main` and carries over only the approved functions' inventory
entries, match records and unit files, so a unit a Drafter is still editing neither enters the
commit nor blocks it; the shared checkout is not touched. Afterwards `next-actions` lists
`python3 tools/flow.py sync`, which fast-forwards the shared checkout, dropping only local copies
byte-identical to the integrated files; if any local file differs it refuses and lists it: that
is a stop for the strong role, never a reason to delete or overwrite a file yourself.

## What each worker returns

| worker | returns | full output |
|---|---|---|
| Drafter | `| unit | functions passed | attempts | result line file |` | queue `results.jsonl`, unit `attempts/` |
| Reviewer | `| function | verdict | category | blocking findings | naming findings |` and the review path | `.local/reviews/<task-id>.md` |
| strong role (Engineer, Sol) | `| item | outcome | attempts | file |` | `.local/handoffs/<task-id>.md` |
| direction check | five lines | `.local/handoffs/direction-check-<n>.md` |

A longer return is a worker fault: do not copy it anywhere; note "long return" in the session
summary.

## Stop and escalate

Stop that group (or everything, where it says so) and report to the maintainer, quoting the tool's
line, for:

1. A Reviewer `escalate` with category `provenance`, `legal` or `systemic` (`[stop]` line).
2. A sampling disagreement: a second Reviewer differs, or a re-run is not AGREE (`[stop]` line).
3. CI `RED` after a push: stop everything that would push until main is green again.
4. A pass that does not reproduce on the second host, or any sign that an accepted function is
   wrong.
5. Any question about a gate, a licence, provenance, exposure of private material to a model, or
   spend beyond the recorded limits.
6. Any proposal to change the comparator, validator, lint, acceptance rule, a recorded gate or
   these instructions.

Hand to the strong model of your profile (a planning-orchestrator or Opus/Sol check), with the
tool output and nothing else, for:

7. A command that fails twice for a reason that is not one of the above.
8. A situation `next-actions` does not cover, two lines that contradict each other, or a worker
   that returns something this file does not describe.
9. The baseline decision `python3 tools/flow.py baseline ...` (which versions are already past
   their first 20 sampled acceptances): never run it yourself.

Never resolve these by editing files, re-running a Reviewer until it agrees, or choosing a
different group order.

## Reports every session

- **Friction report**: `python3 tools/friction.py --write` once per session (a `[run]` line asks
  for it). Read only its first paragraph: if it says the cheap profile is below its threshold,
  add that line to the session summary.
- **Direction check**: after every 200 accepted functions, and at least once per session (an
  `[end]` line asks for it if none ran), run `python3 tools/flow.py brief direction` and start the
  `direction-check` worker (strong model of the profile) with the brief. It edits nothing; it
  writes `.local/handoffs/direction-check-<n>.md`. Then `python3 tools/flow.py event direction-check`.

## End of session

Write `.local/handoffs/orchestrator-<date>.md` with: profile; groups dispatched, integrated
(commits and CI result), held; counts accepted, rejected and escalated; stops reported; the
friction report path and its first paragraph; the direction check path; workers started per role
and model; anything that took a second try. Return the same in at most 15 lines to whoever
started you.

## Never

Commit or push except through `flow.py integrate`; run `accept_function.py` directly; edit a
saved review; start a Reviewer on a function its Drafter or triager would review; give a worker
material its model is not cleared to read; start a Boat machine (Boat is retired; confirm briefs
use the runner hosts); post anything publicly.
