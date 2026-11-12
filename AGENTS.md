# Instructions for all agents and contributors

**Helping an external contributor match a function?** Follow
[docs/contributing-agent.md](docs/contributing-agent.md) for the workflow and skip "Multi-agent
execution" below, everything about Boat, and these project-internal bullets of "Work safely": the
macOS-only tooling note, handoffs under `.local/handoffs`, Engineer commits and pushes, and "Watch
CI"; those are for the project's own agents. "Keep private inputs private" and "Be precise about
evidence" bind every agent, yours included.

## First read

Read `README.md`, `LEGAL.md`, `PROVENANCE.md`, `docs/verification.md` and
`docs/clean-room.md` before research or publication. Claude must read this file too;
`CLAUDE.md` imports it. This repository is independent of Mudcrab: never apply Mudcrab's
Cargo/build/cache instructions here or modify its checkout as part of a research task.

## Keep private inputs private

- Use `.local/` for legally obtained executables, toolchains, databases, raw decompiler output,
  traces, saves and generated objects. Never force-add ignored paths.
- No game files, binary bytes, disassembly, dumps, proprietary symbols/SDKs, leaked code or
  unlicensed copied code in commits, PRs, issues, logs, releases or CI artifacts. One maintainer
  exception: names, declarations and code from the FNV decompilation `momusdigital/fnv_decomp@91e1b6e8`
  may be reused in reconstructions, labelled `SIBLING(...)`, although its LICENSE grants none
  (`docs/authorizations.md`, Notes; `LEGAL.md`). It is never evidence about the Skyrim binary.
- Do not upload game-derived material to an AI/cloud service without explicit owner authorization
  and assessment of the service terms. Permission to research locally is not permission to upload.
  An external contributor may let their own coding agent read listings made locally from their own
  legally obtained copy, under their own account and their AI provider's terms; that is their
  decision and responsibility, and the contributor docs say so and ask once. Nothing game-derived
  goes into the repository, PRs, issues or CI either way (`docs/authorizations.md`, Notes).
- Analyze your own legally obtained inputs. Do not download game binaries from anyone else or
  unofficial PDBs, acquire cracks, or add copy-protection removal instructions/tools. An owner
  fetching their own purchased copy with their own account through Valve's Steam client or SteamCMD
  is fine; the project itself never distributes a game file.
- Stop the affected publication if provenance is uncertain. Record the question without reproducing
  suspect content. Unrelated original tooling work may continue.

## Be precise about evidence

- The target is UNPINNED until `builds/target.json` has real metadata and a locally measured hash.
  Do not invent a version, checksum, compiler, address, test result, cost or completion denominator.
- Address identity is `(build id, RVA)`; never transfer an address between versions without proof.
- Every finding identifies sources, revisions, source exposure, method, limitations and confidence.
  Label inferred names as guesses. Preserve unknowns rather than filling them plausibly.
- Byte match, semantic equivalence, inferred behavior and layout-size agreement are different claims.
- Never mark a function `matched` until the matching gate in `docs/verification.md` is implemented
  and enabled, and then only under its acceptance rule: reproduced comparator pass, Reviewer
  approval, integration. Bootstrap CI checks only publication hygiene, metadata and site
  generation; it does NOT compare against the game.
- Progress comes only from `data/progress.json`; totals are derived, not manually entered into HTML.
  Unknown scope means no completion percentage. No dummy success records or fake history.

## Work safely and leave a usable handoff

- Claim a small issue before a long task. Record human owner, agent/model if used, exact build,
  reproduction command, outcome, blockers and next step. Launch agents only as described in
  "Multi-agent execution" below, or when the human maintainer asks.
- All shell commands run from this repo. Private command paths must stay in local configs.
- Keep ordinary CLI/tooling work on macOS; Windows Arm VM and live Skyrim/SKSE compatibility are
  unverified. Do not install a VM, change a game install or provision paid machines without scope.
- No broad staging: inspect `git diff`, then stage named files. Run `python3 tools/check.py --staged`
  immediately before committing. Never bypass a guard to ship suspect material.
- Before a PR/push run `python3 tools/check.py`, `python3 -m unittest discover -s tests -v`,
  and `python3 tools/build_site.py`. Review all staged text for provenance and secrets. The
  integrating Engineer, or the orchestrator when run with a shell, then commits and pushes; there
  is no per-commit maintainer review.
- Watch CI. Whoever pushes checks the CI result of the pushed commit with
  `python3 tools/ci_status.py --commit <full sha> --wait 600` before reporting the work as done, and
  records the result in the handoff. A red `main` is fixed, or its cause reported to the maintainer,
  before any further push of unrelated work. Green CI proves publication hygiene only, never a match.
- PRs describe evidence and limitations. Do not claim CI proves legality or gameplay parity.
- Protect the research/implementation boundary. Do not port reconstructed functions into Mudcrab
  or declare a specification clean-room-safe just because it is prose or lives in another repo.

## Multi-agent execution

The project runs as one orchestrator directing worker subagents, with deterministic verifier
machines deciding results. Nothing in this section grants an authorization; every gate below
must be recorded in `docs/authorizations.md` by the human maintainer before work that needs it.

### Roles

| role | who | does | never does |
|---|---|---|---|
| Maintainer | awarebayes (human) | grants gates, sets budgets, decides licence and policy questions, handles escalations, reads summary reports, may audit and revoke any accepted function | reviews individual functions (not asked to) |
| Orchestrator (planning) | Claude Fable, latest available (`claude-fable-5-1` today) via `.claude/agents/orchestrator.md` | plans, splits work into tasks, chooses profiles and batch scope, decides the exceptions the routine orchestrator hands up, writes briefs for new kinds of work, triages failures, tracks spend against the cap, reports to the maintainer | writes reconstructions or tooling, judges a match, edits gates, posts publicly |
| Orchestrator (routine) | Claude Sonnet via `.claude/agents/orchestrator-routine.md`, or the profile's orchestrator model through `docs/orchestrator-runbook.md` | runs `tools/flow.py next-actions` and does what it lists: starts Drafters and Reviewers with generated briefs, runs `flow.py integrate` (accept, checks, commit, push, CI), produces the friction report, stops on every exception the runbook lists | decides ordering or sampling, writes briefs by hand, edits files, judges a match, works around a refusal |
| Direction check | the profile's strong model (Opus today) via `.claude/agents/direction-check.md`, fresh context | reads the friction report, pipeline status, recent handoffs and the census; writes `.local/handoffs/direction-check-<n>.md` with what to change | edits anything else, starts agents |
| Engineer | Claude Opus 5.5 (`claude-opus-5-5`) subagent | tooling, comparator, Ghidra/import work, failure analysis on near-misses, integration of worker branches, recording `matched` once the acceptance rule is met, commit and push | marks `matched` without a reproduced pass and a Reviewer `approve` |
| Reviewer | Claude Sonnet subagent by default via `.claude/agents/reviewer.md`; Claude Opus 5.5 (`claude-opus-5-5`) for sampling second passes, confirming non-Opus escalations and machinery reviews; OpenAI Terra under the `claude-low` profile (any model: `docs/reviewer-runbook.md`; admitted classes are set by `docs/verification.md`), fresh context | approves, rejects or escalates reconstructed source per the checklist in `docs/verification.md`; rejects only on its blocking grounds and lists names, labels and wording as non-blocking naming findings | reviews a function it drafted or triaged, edits source, comparator, validator or reports, counts as match evidence |
| Drafter | Claude Sonnet 5.5 (`claude-sonnet-5-5`) subagent | bounded high-volume tasks: reconstruction drafts, synthetic fixtures, report formatting, doc updates | decides scope or accepts its own output |
| Verifier | deterministic job on a runner host from the private runner config (the maintainer's Mac under Wine and Windows PC natively; Boat is retired) | compiles a pinned source revision with the pinned recipe and runs the comparator; emits a sanitized report | involves a model in the pass/fail decision |

Pipeline state lives on disk, not in an orchestrator's context: `tools/flow.py` derives each
function's state (queued, drafting, drafted, confirmed, review pending, approved or rejected,
accepted, pushed) from the queue, records, saved reviews and git, and `next-actions` prints the
steps in order. Workers save full output to files and return a short fixed table.

**Profiles.** `tools/profiles.json` maps each role (orchestrator, drafter, reviewer, strong) to a
provider, model and effort, plus the Drafter's documents, kit and attempt limits:
`cheap` (default: Haiku- or Luna-class Drafters on the small card, skeleton and sheets),
`full` (Sonnet Drafters with the full card and brief) and `claude-low` (OpenAI models through
Codex for orchestration, review and strong work, Haiku or Luna drafting). `cheap` is the default
because weak-model drafting passes the same comparator gate; it stays default only while the
friction report shows its pass rate at or above the threshold in `tools/profiles.json`. A profile
never changes what counts as a match, and a Reviewer model the acceptance rule does not admit is
refused whatever a profile says. Today the rule admits Opus Reviewers only: Sonnet and Terra
Reviewers are prepared and pending a blind calibration against the Opus reviews and a
Reviewer-checked rule change, so every profile's review groups get an Opus Reviewer until then.
What OpenAI models may read under `claude-low` is recorded in `docs/authorizations.md` (Notes).

**Friction and direction checks.** The routine orchestrator produces the friction report
(`python3 tools/friction.py --write`) every work session. A direction check (strong model, fresh
context, `.claude/agents/direction-check.md`) runs after every 200 accepted functions and at
least once per work session, reads the friction report, recent handoffs and the census, and
writes `.local/handoffs/direction-check-<n>.md`; it edits nothing. The planning orchestrator
reads it and acts or escalates.

The planning orchestrator's agent definition can only read files and start or message subagents,
so "no code from the orchestrator" is enforced; the routine orchestrator's shell is for the
commands its runbook and `tools/flow.py` list, and its only commit and push is `flow.py
integrate`; other file changes, including `data/progress.json`, go to a worker, and so does commit
and push unless the maintainer runs the orchestrator with a shell. A model saying a reconstruction "looks right" is never evidence of
a match; only a comparator report counts. The Reviewer is a required sanity and provenance check
on top of that evidence, not a substitute for it. Acceptance of `matched` is automated under the
rule in `docs/verification.md`. Do not ask the maintainer to review individual functions.

Start the orchestrator from the repository root:

```sh
claude --agent orchestrator            # planning and exceptions
claude --agent orchestrator-routine    # routine queue work (docs/orchestrator-runbook.md)
```

Any other harness (Codex, T3) runs the routine loop by pasting the line at the top of
`docs/orchestrator-runbook.md` with the profile name.

### Authorization gates

Recorded in `docs/authorizations.md` with scope, limits, date and grantor. Absent = not granted.

- **G1 local tools**: install JDK, Ghidra and other analysis tools under `.local/` on the Mac.
- **G2 model exposure**: send game-derived text (disassembly, decompiler output, reconstructed
  source) to Anthropic models in prompts or tool results. Until granted, agents may run local tools
  on private inputs but read back only sanitized results: counts, hashes, pass/fail, and RVAs/names
  that come from public community sources. They must not `Read` or `cat` raw game-derived output.
- **G3 paid compute**: provision Boat machines. Must state machine size, maximum concurrent
  machines, spend cap, per-machine auto-stop deadline and deletion/snapshot policy.
- **G4 toolchain on cloud**: install a licensed Microsoft compiler/SDK on remote machines.
- **G5 game data on cloud**: place the target executable, slices of it, or reconstructed source
  on remote machines. G3 alone covers only original and synthetic inputs.

### Phases

Each phase finishes with a checked, pushed commit and a summary to the maintainer. The
orchestrator does not start a phase until the previous one's finish condition from `docs/plan.md` is met and its gates are recorded.

1. **Local foundations** (G1; G2 optional). Three independent tracks run in parallel:
   - Ghidra import and anchor checks, plan step 2, issue #2 (Engineer).
   - Comparator and its negative tests on original synthetic COFF/PE fixtures, step 4, issue #5
     (Engineer, Drafter for fixtures). Needs no game data and no MSVC.
   - Compiler-candidate research from public sources and the pinned target's header metadata,
     step 3 paper part, issue #3 (Engineer).
2. **Single verifier pilot** (G3, G4). One Boat machine: Wine plus the candidate MSVC, synthetic
   C++ compiled twice with identical output, comparator run there, machine stopped and billing
   checked. Issue #4. Record the machine recipe so later machines are clones, not hand setups.
3. **First real function** (G2, and G5 if compiled remotely). Plan step 5, issue #6: one function,
   one Drafter reconstruction loop, Engineer triage of near-misses, verifier report reproduced on a
   second host, the gate change that enables `matched` (Engineer, tests, separate Reviewer pass),
   then Reviewer approval and integration under the acceptance rule.
4. **Fan-out** (all gates, explicit concurrency and spend cap). Only after phase 3 is reproduced.

### Fan-out design (phase 4)

- **Queue**: the orchestrator picks functions from a reviewed inventory slice, each identified by
  `(build id, RVA, size)`. One task = one function; a worker claims it by task id.
- **Draft loop**: a Drafter writes a reconstruction in its own git worktree (`isolation:
  "worktree"`), submits it to a verifier, reads only the sanitized diff summary, and retries within
  an attempt limit set in the brief. Stuck tasks go to an Engineer with the attempt history.
- **Review**: each function with a reproduced pass goes to a fresh Reviewer (never its Drafter
  or triaging Engineer), singly or in a batch. `reject` returns it to the draft loop with reasons;
  `escalate` follows `docs/verification.md`. The sampling safeguard there (at least 5% random,
  plus the first 20 per new recipe, compiler, Drafter or Reviewer prompt version or acceptance-rule
  version, and the first 20 label-only re-acceptances under each acceptance-rule version) gets a second Reviewer and a
  from-scratch comparator re-run; a disagreement pauses that batch and escalates.
- **Verifier hosts**: the runner hosts in `.local/verifier/runners.json`
  (`tools/verifier/runners.py`), all at the same comparator commit and recipe, each with its own
  hash-checked toolchain and image. Every pass is reproduced on two hosts that are different
  machines with different OS loaders (`docs/verification.md`, Runner hosts) before it is
  reported. Hosts carry only the inputs their gate allows and never run untrusted PR code.
- **Boat use**: Boat is retired; its verifier machines were deleted (`docs/authorizations.md`,
  Notes). Bringing it back is a maintainer decision. Until then no agent starts a Boat machine;
  if it returns, every agent that touches one follows `docs/boat-agent-guidelines.md`
  (`session up --boat`/`down`, no per-unit forks, keep the starts reserve, buy nothing, record
  compute and starts in the handoff).
- **Budget**: the orchestrator tallies subagent runs, and machine-hours of any paid compute,
  against the caps from worker reports and stops dispatching at a cap. Runner hosts cost no
  machine-hours; the G3 cap applies to Boat use only.
- **Integration**: an Engineer merges passing, Reviewer-approved worktree branches, reruns the
  full checks and the verifier on the integrated tree, records `matched` with
  `tools/accept_function.py` (which writes the sanitized Reviewer record), then commits and pushes.
  For a review group of `tools/flow.py`, `python3 tools/flow.py integrate <group>` is that step as
  one command that stops at the first failure; it builds the commit in its own worktree at origin,
  carrying over only the approved functions' entries, records and unit files, and `flow.py sync`
  then fast-forwards the shared checkout. Claims refer to integrated source only. The maintainer gets periodic summaries, not commits.

### Worker briefs and handoffs

Every brief from the orchestrator states: task id, plan step and issue, gates in force and what
they forbid, allowed inputs, the exact output paths, acceptance criteria, attempt and time limits,
and "do not push, post publicly, mark `matched`, or start further agents." Only an integration
brief lifts the push and `matched` parts, and only for work that meets the acceptance rule; the
Reviewer brief also names the functions, source revision and report paths. Every worker writes a
handoff to `.local/handoffs/<task-id>.md` (model, inputs and their revisions, commands, outcome,
blockers, next step) and returns its summary. A Reviewer's full review is stored at
`.local/reviews/<task-id>.md`, with a sanitized verdict record alongside the public report
(`reports/<build id>/<rva>.review.json`). The
orchestrator works from handoffs and reviews, not memory, and reports gate blockers and the
escalations listed in `docs/verification.md` to the maintainer rather than working around them.
