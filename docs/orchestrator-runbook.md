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
admits Opus by default and `gpt-6.1-terra` under `claude-low`; Sonnet is pending calibration and
a Reviewer-checked rule change. Under `claude-low`, Sol is admitted for any review and Terra
is the default first Reviewer; exactly `gpt-6.1-sol` is the strong Reviewer
for sampling second passes, confirmation of non-Opus escalations and reviews of comparator,
validator, verifier and acceptance-rule changes. Sol was admitted by maintainer decision WITHOUT
a calibration ("sol is goood enough dont waste time"); Terra's admission followed calibration.
Every second pass under `claude-low` uses a different model from the first review; an initial
Sol review therefore needs Opus. Opus keeps these duties outside `claude-low`. Independence is
per run: fresh context, never the run that drafted, engineered, triaged or first-reviewed the
function. A profile Reviewer the rule does not admit is replaced by Opus with a note; a sampling pass with no admitted independent model is refused.

A Codex worker that should follow a runbook gets the runbook line: Reviewer
`Read docs/reviewer-runbook.md and follow it. Your brief is <brief path>.`; Drafter
`Read docs/drafter-runbook.md in this repository and follow it exactly. Your worker label is <label>.`

After a successful push, both `flow.py integrate` and `integrate-family` run claim synchronization.
A failure prints a warning and leaves integration successful; retry with `python3 tools/claims.py sync`.
Sync counts only acceptances on `origin/main`, updates the accepted count, and comments and closes
an issue when every member is accepted. It leaves unknown range members open. Fetch origin before
running sync manually. Issues without the new claim block are left alone.

## The loop

1. `python3 tools/flow.py session-start --profile <profile>` (once per session). It prints which
   model does each role. Then run `python3 tools/claims.py publish --dry-run` and
   `python3 tools/claims.py publish` to expose every queued, drafted and confirmed unaccepted
   function on GitHub. This publishes only build ids, RVAs, counts and names from committed
   inventory, assigned to the authenticated GitHub user. It never publishes task paths or notes.
   `publish` is idempotent and groups work by queue, family or static cluster (at most 15 issues).
   Additional family checkouts and static member/range manifests may be supplied with
   `--family-root` and `--cluster-list`, or ignored `.local/claims-config.json` settings
   `family_roots` and `cluster_lists`. A cluster manifest holds `build_id` and `clusters`, each
   with `members` (RVA values or objects with `rva`) and optional `ranges` (`start`, `end`).
   Ranges must cover the member starts; use only ranges known not to reserve unrelated work.
   Set `project_login` in that local config only to override the authenticated user's login.
   `work_queue.py add` and `next` skip units containing other people's live claims, reporting the
   issue; their `--refresh` option bypasses the ten-minute cache. Offline reads warn and use stale
   claims without stopping the pipeline.
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

## Approved subsets (Engineer)

When rejected or disputed members hold an individual group, an Engineer may run
`python3 tools/flow.py split-group <group> --functions <RVA or id> ...` to freeze an explicitly
approved subset. The original group, saved verdicts and sample draw stay unchanged. The subset
retains every selected member's original second-pass requirement. If too few original sampled
members remain to cover 5%, it adds a deterministic random sample and writes new second-review
and clean-rerun briefs; finish those before integration. A selected disagreement still refuses.
Integrate the returned subgroup with `--approved-only`. Only its selected inventory entries,
records and required unit files enter acceptance. Rejected and disputed members stay held.

A shared unit is copied whole, so its changes can stale other acceptances. Re-confirm and
re-review affected accepted functions under "Stale acceptances and delta reviews" before the
unit and renewed evidence land together. Splitting never exempts a family member, clears a
rejection or escalation, or permits a stale unit through the staged check.

## Family batches

`next-actions` also prints family review needed, draw sample, review sample and accept batch
steps. The planning orchestrator and Engineer choose a bounded family and batch; the routine
orchestrator never picks parameters, ranges, the population or a seed. A family is the generator
or stamp template plus version and template digest, bound to the target build, recipe, compiler
and comparator. Any change starts a new family. Each member carries its parameter row and
name-source label; a comparator pass proves no name.

Engineer setup (no verifier or acceptance is performed by these metadata commands):

1. Prepare a private JSON spec with `origin`, `binding`, `template_source`, `parameter_source`,
   `parameter_ranges` and `first_members` (the first 20 enrolled inventory ids, in order).
   `binding` is `family_review.binding(fn, match_record)`; each source has `path` and `sha256`.
   Run `python3 tools/flow.py family-plan --spec <spec>` to freeze member digests, write the
   public manifest under `reports/<build>/families/`, and generate its Reviewer brief.
2. If the first 20 are confirmed and ungrouped, planning creates one normal group and a combined
   brief: one fresh admitted primary Reviewer writes both the family JSON and their individual
   review blocks in one pass. The independent second-pass safeguard still applies. Integrate the
   first 20 normally before approving the family. Already-reviewed first 20 keep their normal
   evidence and safeguards. Start the family Reviewer on the generated brief; its JSON format
   and checklist are in `docs/reviewer-runbook.md`, "Family reviews". `family-approve <manifest>
   --review .local/reviews/<task>.family.json` checks the saved approval and all 20 safeguards.
3. `python3 tools/flow.py family-batch <manifest> --name <batch> --seed <seed> --functions <ids...>`
   freezes the complete later population, including member digests. Stage the metadata by name,
   run `check.py --staged`, and commit it before `family-draw <batch path>`. Commit the drawn
   batch before any population member is accepted. These metadata commits belong to the Engineer;
   the routine orchestrator hands an uncommitted metadata refusal to the strong role.

To correct a family before approval, `python3 tools/flow.py family-plan --spec <corrected-spec>
--supersede <old-manifest>` preserves the old paused manifest with a replacement pointer, archives
its saved review files under `.local/reviews/superseded/`, releases its review groups and creates a
fresh family plan and briefs. The replacement keeps the same origin, binding and first 20. The
command refuses an approved family, a family with a batch, or accepted first-20 members; use the
pause and revocation procedure for accepted evidence. Archived reviews are not approvals of the
replacement. Resolve any independent provenance or policy escalation under the existing rule.

The draw ranks population ids by SHA-256 of canonical JSON `[seed, function_id]`, breaking ties
by id, and takes `min(population, max(20, ceil(5%)))`. The public batch preserves seed, full
population, member hashes, pre-draw commit and sample. The gate checks that the planned metadata
was committed before selection, the draw was committed before acceptance, and no population
member had already been accepted at that exact origin and row in that history. Never redraw,
shrink a population or change a seed after seeing the sample.

The ordinary `review-group` excludes eligible unsampled members, reviews all sampled members
and all parameters outside the approved ranges, and keeps every existing second-pass safeguard.
`integrate-family <batch path>` accepts the remaining unsampled in-range members only after
those individual reviews and safeguards pass, in the same isolated integration/check/commit/push
path as ordinary groups. The acceptance tool requires the actual saved approving family review,
an admitted model, active family, exact origin/version/digest and target bindings, unchanged
member rows and the committed draw. Other functions keep individual review; a family approval
cannot be carried by label-only acceptance. No family command changes the comparator or lint.

On sampled rejection, binding error, non-reproduction, provenance doubt, Reviewer disagreement
or another material defect, stop the whole family and run `family-pause <manifest> --reason
'<short public reason>'`. Commit the pause by name after the staged check. Assess the affected
population, explicitly revoke accepted members whose evidence is invalidated, and escalate
policy/provenance or systemic doubt under the existing rules. A pause freezes new acceptance;
existing records stay auditable until explicit revocation. Correct the cause and use a freshly
reviewed family version before resuming. Never clear a pause by hand or retain invalidated
acceptances silently.

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
   A non-Opus escalation stays held for independent strong Reviewer confirmation (Sol under
   `claude-low`, Opus otherwise); report to the maintainer only if the confirmer also escalates.
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

Commit or push except through `flow.py integrate` or `flow.py integrate-family` (Engineer metadata
commits are described above); run `accept_function.py` directly; edit a
saved review; start a Reviewer on work it drafted, engineered or triaged; give a worker
material its model is not cleared to read; start a Boat machine (Boat is retired; confirm briefs
use the runner hosts); post anything publicly.

When the profile has a fallback Drafter, `next-actions` offers failed first-tier units through `brief drafter --tier fallback`; dispatch the specified model with that brief. Fallback results and counted attempts are recorded separately from the first tier.

## Importing isolated family state (Engineer)

`python3 tools/flow.py import-state <worktree>/.local/flow --reviews <worktree>/.local/reviews`
imports an isolated worktree's private review scheduling state into this repository's shared
`.local/flow`. Run it before replacing the source directories with links to the shared ones.
The source must be another worktree of the same repository. It validates match records, unit
and first-member digests, family template/extraction pins, saved family approvals and sampling
rerun records against that worktree. A mismatch refuses the import before publishing state.

The receipt under shared `.local/flow/imports/` records the input hashes, fresh group ids,
review filenames and unchanged review-file hashes. Saved reviews retain their original task
titles and bytes; an imported group's `saved_review` locates the renamed file. Unsent reviews
get new task ids and collision-checked briefs in the shared checkout, with explicit paths
and instructions to review the source worktree. Combined family instructions are retained. Import preserves dispatch and
sampling records, but does not activate families, accept functions, replay session events or
import sampling version baselines. Family plans and original events are retained as private
snapshots; generated public inputs remain in their source worktree. Continue the family steps
from that source worktree, using the shared flow and reviews directories.

An identical import is idempotent, including after normal progress of its imported groups.
Different existing files are never overwritten. A partially written import blocks other flow and acceptance commands until it resumes with its
recorded id mapping. Direct acceptance takes the same lock; integration passes its locked
descriptor to the acceptance subprocess without releasing ownership. Keep the source state unchanged until import completes. Flow CLI operations
use a permanent advisory `.state.lock` in their resolved flow directory; readers also lock so
multi-file mutations stay consistent. Group and version JSON use atomic replacement. Run the
updated tooling in every concurrent orchestrator; older processes do not participate in this
lock. An integration holds the lock through checks, push and CI; other commands wait for it.
