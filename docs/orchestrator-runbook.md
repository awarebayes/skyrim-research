# Orchestrator runbook (routine queue work, any model)

## Ten-line lane guide

1. Use green-main tools and the shared `--flow-dir`; keep approved input roots and committed tooling tips available until their receipts finish.
2. Enqueue functions with `integrate`, `integrate-groups`, `integrate-family` or `integrate-labels`; enqueue all ready work first.
3. Commit named tooling files after the staged guard, then run `tooling-push --wait-lane`; all tooling queued before the lease is taken shares one candidate.
4. Run `lane-run --wait-lane` to drain the queue; CLI calls wait by default, and `--no-wait-lane` is an explicit nonblocking probe.
5. After push, the lease is released during exact-SHA CI; the next candidate checks in parallel and may push only after its origin SHA is GREEN.
6. `lane-status` gives exact resume commands; dead local unpublished owners are skipped automatically, while conflict/stale inputs and candidates remain intact.
7. Builds require Python 3.13 with pyexpat and 3 GB free; below the 10 GB soft floor only explicit `--allow-low-disk` admits a new heavy job.
8. Preview `cleanup --dry-run`, then opt in with `cleanup`; working files alone may be removed, evidence and Git refs/stashes remain; `sync` after GREEN.

Follow `docs/anti-eu-bureaucracy.md`: ship in bulk, decide rather than stop, and add no ceremony beyond named rules.

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
   run by the push lane (`flow.py lane-run`). Never claim a pass, an approval or a green CI a tool did not print.
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

After a successful lane push, `flow.py lane-run` runs claim synchronization.
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

`flow.py integrate <group>`, `integrate-groups <groups...> --name <batch>` and
`integrate-family <batch path>` enqueue the existing selections and return immediately. Keep
the source checkout and its approved inputs available until the lane finishes. The queue records
the input root, selection and options under `.local/flow/lane/`; `lane-status` prints its receipts.
Label-only re-acceptances use `integrate-labels --functions <ids or RVAs...>`; their existing
code-section, provenance and sampling requirements remain unchanged.

Every new lane build and `tools/verifier/confirm` invocation has a 3 GB hard minimum (decimal).
A configurable soft floor defaults to 10 GB: `--soft-free-gb` or `SKYRIM_SOFT_FREE_GB`.
Tooling validation uses the same admission policy. Below the soft floor, a job warns and refuses
unless `--allow-low-disk` is explicitly supplied. That flag
never overrides the 3 GB hard minimum. The lane's existing `--min-free-gb` / `SKYRIM_LANE_MIN_FREE_GB`
can request a higher minimum; neither can admit a new build below 3 GB.

Run `python3 tools/flow.py lane-run` after enqueueing all ready work. One runner takes everything
queued at its start, carries only the approved input through the existing acceptance path into
one isolated local clone at current `origin/main`, rebuilds the index once, stages named files,
runs `check.py --staged` and makes one combined commit. It runs `check.py`, the full unit suite
and `build_site.py` once on that exact commit, pushes it, and waits for exact-commit CI with
`ci_status.py`. Work enqueued during the run remains queued for the next run. `--run` on an
integration command enqueues and runs the lane; `--no-push` also runs it, stopping after checks.
Resume a failed check or pending CI with `lane-run`; it retains the candidate and checkpoint.
A red CI stops the lane before any later push.

An individual acceptance failure is recorded with its reason and excluded; successful members
still ship. Family binding/sampling failures hold the entire family batch, never shrink its
committed population. A whole-tree check failure stops the run without pushing. Inspect dropped
items in `lane-status`, fix their evidence and enqueue them again. Missing inputs or conflicting
source closures are refusals, not permission to overwrite them. If origin moves, the lane checks
for overlapping inventory/source changes, replays the combined selection on the winner and
reruns all required checks. It never pushes an unchecked rebased tree.

`.state.lock` protects queue snapshots and short state/receipt writes. It is released throughout
acceptance, checks, push and CI; a separate nonblocking `.lane.lock` admits one runner. Record-only
commands and review saves can proceed during a lane run. Candidate clones and failed attempts
are retained. No lane operation prunes worktrees, branches or stashes; cleanup is opt-in through
`flow.py cleanup` (preview with `--dry-run`). It considers only DONE+green lane trees, harvested
drafts without claims, and AGREE reruns. Dirty/locked trees and queued inputs stay intact.
JSON, text logs and worktree-registration logs are archived under `.local/flow/cleanup/`.
Independent lane clones keep `.git` in place so borrowed objects, refs and stashes stay usable;
only their working files are removed. Registered worktrees use plain `git worktree remove`,
without force, pruning or branch/stash deletion. Afterwards `flow.py sync` fast-forwards the shared checkout, replacing
only local copies byte-identical to origin; differing files refuse and stay intact.

Tooling publications also use the lane: `flow.py --root <committed-tooling-checkout> --flow-dir
<shared-flow> tooling-push`. For Git worktrees its default flow directory comes from the common
Git directory; independent clones must name the shared flow explicitly. It refuses a busy lane
(or waits with `--wait-lane`),
runs the full checks once per final tree, rebases/rechecks a lost race, pushes and watches CI.
`lane-status` reports dead owners using PID, host and process birth, including legacy runs after
their lock is free; its resume/retire commands preserve the receipt and candidates. A pushed run
can resume CI but cannot be retired. No run is automatically retired.

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
fresh family plan and briefs. The replacement keeps the same family name, binding and first 20.
If its source origin changes, both its version and template digest must change; its members need
fresh confirmation and review under that new origin. No old approval carries into the replacement. The
command refuses an approved family, a family with a batch, or accepted first-20 members; use the
pause and revocation procedure for accepted evidence. Archived reviews are not approvals of the
replacement. Resolve any independent provenance or policy escalation under the existing rule.

The draw ranks population ids by SHA-256 of canonical JSON `[seed, function_id]`, breaking ties
by id, and takes `min(population, max(20, ceil(5%)))`. The public batch preserves seed, full
population, member hashes, pre-draw commit and sample. The gate checks that the planned metadata
was committed before selection, the draw was committed before acceptance, and no population
member had already been accepted at that exact origin and row in that history. Never redraw,
shrink a population or change a seed after seeing the sample.

An Engineer may combine the committed family metadata and sampled acceptance in one push with
`flow.py integrate <sample-group> --with-metadata`. Unpublished commits may change only family
manifests or batch JSON, without deletions. The tip must descend from current origin; a merge may
preserve moving main only through a parent already on origin, with only metadata added to that base.
The metadata must validate and match its committed content. The seed/population and draw commits
may contain only the exact tip snapshots or the canonical pre-draw batch (null commitment/sample),
so an invalid intermediate blob cannot hide behind a repaired tip. These commits
remain separate ancestors before acceptance; source, tooling and other unpublished changes are
refused. All ordinary review, comparison, staged, clean-tree and CI gates still run.

The ordinary `review-group` excludes eligible unsampled members, reviews all sampled members
and all parameters outside the approved ranges, and keeps every existing second-pass safeguard.
`integrate-family <batch path>` accepts the remaining unsampled in-range members only after
those individual reviews and safeguards pass, through the same push lane as ordinary groups.
The acceptance tool requires the actual saved approving family review,
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

At session start run `python3 tools/flow.py worktrees list`; at session end run `python3 tools/flow.py worktrees prune`.

## End of session

Write `.local/handoffs/orchestrator-<date>.md` with: profile; groups dispatched, integrated
(commits and CI result), held; counts accepted, rejected and escalated; stops reported; the
friction report path and its first paragraph; the direction check path; workers started per role
and model; anything that took a second try. Return the same in at most 15 lines to whoever
started you.

## Never

Commit or push except through `flow.py lane-run` or an integration command with `--run`
(Engineer metadata commits are described above); run `accept_function.py` directly; edit a
saved review; start a Reviewer on work it drafted, engineered or triaged; give a worker
material its model is not cleared to read; start a Boat machine (Boat is retired; confirm briefs
use the runner hosts); post anything publicly.

When the profile has a fallback Drafter, `next-actions` offers failed first-tier units through `brief drafter --tier fallback`; dispatch the specified model with that brief. Fallback results and counted attempts are recorded separately from the first tier. The strong tier dispatches only after fallback finishes with unpassed functions; use `work_queue.py hold <unit> --reason <reason>` and `unhold <unit>` to control dispatch.

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
recorded id mapping. Direct acceptance takes its repository state lock. Lane acceptance operates
on a private scheduling snapshot in an independent local clone, so it never holds the live state
lock while validating or rebuilding. Keep source state unchanged until import completes. Flow
CLI operations use a permanent advisory `.state.lock` in their resolved flow directory; readers
also lock so multi-file mutations stay consistent. Group, queue and receipt JSON use atomic
replacement. Run the updated tooling in every concurrent orchestrator; older integration
processes retain their old whole-run lock until they finish.

## Pipelined publication and tooling batches

`tooling-push --wait-lane` records the clean committed input before waiting. A new runner takes all
currently queued tooling tips into an independent retained candidate. Input checkouts are never
rebased or reset. Merge conflicts drop only that input, with its reason. A combined check failure
first proves the baseline, then isolates failing inputs using checked prefixes; a failed baseline
stops the whole run. The successful common path runs full checks once.

Queued review groups can share this candidate through the unchanged accept/carry path. Tooling
that changes gate machinery (validator, comparator, acceptance, review parser, verifier or lane)
publishes separately before function work; those functions remain queued. Every member still
passes its original gates. Arrival during a run belongs to the next run.

The build lease ends immediately after push, recorded as `lane_hold_seconds`. Exact-SHA CI and
post-CI bookkeeping run outside it, including `--resume` of a pushed checkpoint. The next run
may check on top of that pushed SHA but must see its CI GREEN immediately before pushing.
A RED or unavailable result aborts the new push. A failed rebase becomes a terminal `conflict`
receipt with an owner resume command. A dead local unpublished owner becomes `stale` at the next
lease, retaining every input and candidate; `--resume <id>` recovers that checkpoint explicitly.
Live owners are waited on, not treated as foreign resume requests.

`SKYRIM_LANE_PYTHON` may select the interpreter, but it must be Python 3.13 with working pyexpat.
The complete standard unittest discovery inventory runs via `tools/test_suite.py` in isolated
module processes, preserving module/class fixtures and reporting every test. Existing unittest
environment decorators retain their usual meaning; no tests are excluded by the runner.
CI uses the same Python 3.13 runner. Infrastructure performs diff hygiene, metadata/lint, the full
suite and the site build; Pages consumes only its successful artifact for the exact same SHA,
then deploys. This removes duplicated work across workflows, with no check removed.

A lane run may carry approved sampled members and their family bulk together. It applies the
prepared individual reviews through the normal validator first, without rebuilding the derived
index, then runs the unchanged family gates against that provisional state. The final transaction
validates everything and rebuilds the index once. Planning, dropped requests or any final failure
restore all provisional public files; no sampled or unsampled member gains an exemption.
