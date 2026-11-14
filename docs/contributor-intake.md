# External contributions: intake into the acceptance pipeline

How a pull request opened with `tools/contrib.py submit` becomes an accepted function. Nothing here
changes the acceptance rule in `docs/verification.md`; an external pull request enters it at the
same point as a Drafter's worktree branch.

## Flow

1. **CI** (`.github/workflows/contrib-intake.yml`, GitHub-hosted, no secrets, no game data) runs the
   contributor-scope checks from the base branch's tools against the pull request's files read as
   data: only `reconstruction/<area>/<Class>.{h,cpp}`, at most 64 KiB per file, and the source lint
   (`tools/lint_reconstruction.py`, which also checks `SIBLING(...)` labels and `Sibling source:`
   lines name the one allowed FNV revision). `check.yml` runs the usual infrastructure checks.
   This job is **advisory**: a `pull_request` workflow runs as the pull request defines it, so a
   pull request that edits the workflow can change what it checks. The Engineer's local re-run in
   step 2 is the authoritative intake.
2. **Automatic pick-up and Engineer screen.** `tools/contrib_autopilot.py run-once`, called
   every ten minutes, selects the oldest non-draft PR per contributor. Only
   `reconstruction/<area>/<Class>.{h,cpp}` targeting main is eligible; other PRs receive
   `needs-maintainer` and a sanitized explanation. It fetches
   `git fetch origin pull/<n>/head:contrib/pr-<n>` and runs main's
   `tools/contrib.py intake --base origin/main --head contrib/pr-<n>` against blobs read as data.
   Intake failures receive `needs-changes`. It never checks out a PR tree, executes its code,
   or uses its workflows, tools or hooks. A deterministic screen bounds input paths, directives,
   macros/templates, size, line count and encoding, including the complete include closure.
   A fresh `gpt-6.1-sol` Engineer run then reads the diff and unpublished history in a read-only
   sandbox with a fixed screening checklist; anything except SAFE stops before compiling.
   **Maintainer decision (awarebayes, 2026-11-14, p123 session): routine contributor intake,
   verification, review and merge have zero human steps. The pre-compile read is an Engineer
   agent's job, the Reviewer is a fresh admitted run, and the verifier stays deterministic.
   The maintainer accepts the residual risk of compiling untrusted C++ on the verifier hosts
   after the automated screens.** This changes no acceptance, lint, validator or comparator rule.
3. **Confirmation.** The project's existing `tools/ghidra/export_pack.py` writes private unit
   task directories; the ordinary attempt/bind path resolves symbols, then
   `tools/verifier/confirm` independently compiles and compares on the configured Wine and native
   Windows hosts. The contributor's local summary is never evidence. An unavailable Windows host
   is sent Wake-on-LAN on ports 9 and 7, then probed within a bounded wait. Each host's compiler
   has a 180-second timeout that terminates its process tree, including after an SSH disconnect.
   Confirmation is checkpointed per function so a failed comparison need not discard other passes.
4. **Review.** A fresh `gpt-6.1-terra` Reviewer runs through `codex exec` under the admitted
   `claude-low` profile and follows `docs/reviewer-runbook.md`. The usual flow sampler selects the
   first 20 under new components and at least five percent at random. Required second passes
   use a different, fresh `gpt-6.1-sol` run and a from-scratch two-host comparator re-run from a
   clean main checkout with the frozen inputs. Saved reviews remain under `.local/reviews` and
   are parsed by the unchanged acceptance tools. Non-Opus escalations receive their required
   strong confirmation; disagreements and exceptional escalations retain the existing holds.
   FNV material follows the same source, exposure and provenance rules as internal drafts.
5. **Integration.** Approved selections enqueue with `flow.py integrate --approved-only` and
   publish together through `flow.py lane-run --wait-lane`, which invokes
   `tools/accept_function.py` and all ordinary acceptance checks. The acceptance commit is a merge
   with the original contributor head as an additional parent, preserving the exact contributor
   commits and their authors without squashing or checking out their trees. Its tree contains
   the accepted carried inputs; its message adds `Co-authored-by: <name> <email as in the
   contributor's commit>` for each contributor. Unpublished history is screened too, because the
   merge retains it. After the pushed acceptance SHA has green CI, the autopilot posts that SHA
   and closes the PR if GitHub has not already marked it merged. If the contributor changed the
   PR head while a receipt was settling, the old receipt completes without closing the revised PR.
6. **Failures.** Comments contain only sanitized blocking reasons, never bytes, listings or
   private paths. Ordinary failed members are dropped from acceptance and the remaining approvals
   ship. Source in a shared translation unit can include an unaccepted function; it is never
   counted as matched. A real provenance/publication doubt quarantines the PR history, since
   preserving its original commits would otherwise publish that material. No acceptance rule is
   bypassed to keep the routine path automatic. The contributor revises and the new head starts
   a fresh intake; operational failures resume the frozen revision on the next scheduler tick.

The project's own planners (`tools/ghidra/export_pack.py plan`, including `--order cheap` and the
table order) skip RVAs named by an open, unlapsed claim issue or pull request
(`claim: <build> 0x<rva> ...`); offline they warn and plan without that check.
`python3 tools/contrib.py next --json` lists only unclaimed functions. Contributors pick from
`mapped` inventory rows, which can also be in one of the project's own batches: before dispatching
a Drafter on a mapped function, the orchestrator compares the batch with the open claim issues.

## Running and scheduling

Use the maintainer's trusted main checkout and Python 3.13. `gh` uses the maintainer's account;
`codex exec` starts fresh ephemeral read-only Sol/Terra runs. Existing private export and runner
configs and the recorded model-exposure permissions are required. No paid machine is provisioned.

```sh
python3.13 tools/contrib_autopilot.py run-once --dry-run --pr <number>
python3.13 tools/contrib_autopilot.py write-launchd
# Only after inspecting the dry run, from the main checkout:
launchctl bootstrap "gui/$(id -u)" "$PWD/.local/contrib-autopilot/com.skyrim-research.contrib-autopilot.plist"
```

`write-launchd` prints the exact install command. It only writes an ignored private plist;
installation is separate. The job has `StartInterval=600`, with a permanent nonblocking process
lock, atomic state in `.local/contrib-autopilot/state.json` and private logs alongside it. A
scheduler crash reuses successful intake, screen, export, per-function confirmation and review
checkpoints, reconciles GitHub comment markers and lane receipts, and never substitutes a local
contributor report for evidence. Interrupted compiles/model calls are charged before retrying.

Optional `.local/contrib-autopilot/config.json` keys: `max_functions` (60), `daily_compiles` (240),
`daily_reviews` (80, including Engineer screens), `command_timeout` (120 seconds),
`confirm_timeout` (1200), `model_timeout` (1200), `export_timeout` (1800), `wol_mac`,
`wol_broadcast` and `wol_wait` (180). Daily limits reset at UTC midnight; each host compilation
counts separately, including attempts and sampling reruns. `standard_headers` may narrow the
fixed compiler-header allowlist; community headers must resolve inside the repository's
`reconstruction/` include closure, never a private source checkout. Input screens cap each file
at 64 KiB, 2,000 lines, 4,096 characters per line, nesting at 32, macros at 128 and estimated
macro expansion at 100,000 tokens. Unpublished histories are limited to 100 ordinary commits
and a 1 MiB diff. These are intake/resource limits, not changes to the match gate.

Unknown contributor drafting prompts get a separate first-20 component per PR head.

Dry runs perform real screens, exports, confirmations, reviews and acceptance preparation, so
consume the same daily budgets. They keep separate PR checkpoints, flow groups and review directories, never post,
label, merge, close, enqueue into the live lane or push. Their synthetic integration tests need
no game input, network, compiler or model account.

## Threat note: compiling contributed source

**Maintainer decision (awarebayes, 2026-11-14, p123 session): contributor PRs are verified,
reviewed and merged with zero human steps in the routine path. The maintainer knowingly accepts
the residual compiler-exploit risk after the deterministic screen and fresh Sol Engineer diff
read.** An Engineer agent performs that read; the Reviewer remains a separate fresh admitted
run, and all match decisions remain deterministic. This decision concerns compiling source as
input; PR executables, scripts, tools, workflows and hooks are never executed on verifier hosts.
It does not waive a provenance doubt, a sampling disagreement, or any acceptance requirement.

- **Compiler attack surface.** The pinned compiler parses attacker-chosen C++. A malicious input
  can still exploit an unknown parser bug or consume resources despite these conservative
  screens; this is not a sandbox proof. Verifier bundles carry no account credentials; GitHub actions stay in the maintainer process. Both the
  deterministic and Engineer AI screens must pass before the first compile; every compiler
  process tree is bounded to 180 seconds by a dedicated host supervisor, which retains its deadline
  if the outer process or SSH session dies. A Windows Job Object owns all compiler descendants;
  POSIX compiles use an owned process group. Model prompt injection and lexical
  obfuscation remain residual risks; source is expressly untrusted data in fixed model prompts.
- **Includes and paths.** The additional screen checks the transitive repository include closure
  and a narrow pinned compiler-header allowlist. Absolute/parent paths, encoded escapes, symlinks,
  macro includes and non-regular source blobs are refused. The existing source lint, closure
  checks, cleared `INCLUDE`/`CL`/`_CL_` environment and `/showIncludes` host checks remain mandatory.
- **Directives and exhaustion.** The screen refuses assembly, allocation/codegen declspecs,
  imports, token pasting and pragmas except `once`, `pack` and `warning`, including continuation
  and comment tricks. Macro/template, file/line and UTF-8/control-character caps precede the AI
  screen. These conservative checks can reject benign complex source; a refusal is reported,
  never worked around by weakening lint or acceptance.
- **History and publication.** Only unit blobs are materialized over a trusted main checkout.
  Original commits are retained only after approved source passes the ordinary acceptance lane.
  A PR's historical blobs and commit messages enter the Engineer screen too. Public comments use
  the publication filter; raw outputs stay private. Authorship is retained, not treated as proof
  of rights or provenance.
