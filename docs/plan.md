# Execution plan: from this checkout to the first verified Skyrim function

Follow the numbered steps in order. Each step has a finish condition; a later step must not
silently assume an earlier one succeeded. This plan does not itself authorize paid provisioning,
proprietary uploads, VM installation or implementation transfer into Mudcrab.

**First milestone:** one small Skyrim function reconstructed, compiled and independently
rechecked against a pinned executable, with a reviewed public metadata report.
**Second milestone:** one useful behavior specification reviewed for possible Mudcrab transfer.

Current starting point: repository, policies, tests, issue queue and progress website exist.
The target, analysis environment, compiler and matching pipeline are not established.
Reading or committing this plan does not complete any of those research tasks.

## 0. Check the workspace and research boundary

- [ ] Open this repository as its own project in your editor or agent.
- [ ] Read [AGENTS.md](../AGENTS.md), [LEGAL.md](../LEGAL.md), [PROVENANCE.md](../PROVENANCE.md),
  [verification](verification.md) and [the Mudcrab boundary](clean-room.md).
- [ ] Decide who will inspect binary/reconstructed code and who will independently implement
  resulting specifications. Record relevant exposure; do not assume a new chat removes it.
- [ ] Run these commands from the repository root:

```sh
mkdir -p .local/analysis .local/experiments .local/reports
python3 tools/check.py
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
git status --short
```

**Finish when:** checks pass, private directories are ignored, and source-exposure roles are
understood. Resolve any pre-existing local changes before another agent edits the same files.
The generated `dist/index.html` is a local preview, not evidence of research progress.

## 1. Select and fingerprint the executable

Issue: [#1 — Pin the target](https://github.com/awarebayes/skyrim-research/issues/1).
Prerequisite: step 0. This is the first hands-on task.

- [ ] Locate `SkyrimSE.exe` from your legally obtained installation; keep it outside the repo.
- [ ] Establish its actual store and game version from that installation. Do not use a guessed
  version or a toolkit archive filename. Record how the identity was established.
- [ ] Produce the local candidate, replacing all three placeholders:

```sh
python3 tools/fingerprint.py \
  '/path/to/your/SkyrimSE.exe' \
  --store 'actual store' \
  --version 'actual version' \
  > .local/target-candidate.json
```

- [ ] Review the candidate. The command checks PE architecture and hashes the file; it does
  not authenticate the release version or establish that machine code is ready for analysis.
- [ ] Assign a unique lowercase build ID, fill `builds/target.json` with reviewed metadata,
  and set the identical `target_build_id` in `data/progress.json`. Keep scope totals `null`.
- [ ] Run the publication routine below; commit only the metadata and research explanation.

**Finish when:** one reviewed build ID resolves to a real local image hash, store, version and
architecture, and the metadata passes validation. No executable has been published or uploaded.
If a later analysis input differs, record that identity separately through a reviewed manifest
extension; never silently reuse a hash/address map from a different image.

## 2. Reproduce static analysis on the Mac

Issue: [#2 — Ghidra import](https://github.com/awarebayes/skyrim-research/issues/2).
Prerequisite: step 1.

- [ ] Check current upstream Ghidra/JDK requirements for Apple Silicon before installation.
  Follow [macOS setup](setup-macos.md); record exact versions and available disk.
- [ ] Obtain the appropriate community type archive and address mappings for the target.
  Check licensing/provenance and record revisions, artifact hashes and runtime variant.
- [ ] Create a Ghidra project under `.local/analysis/` and import the pinned executable.
- [ ] Establish that representative code regions are analyzable. If they are not, record the
  blocker and obtain maintainer guidance on a lawful input/workflow; do not invent function
  boundaries or add copy-protection removal instructions to this repo.
- [ ] Apply the types and address mappings. Spot-check several independent anchors against
  the actual code and structures; distinguish size checks from verified field offsets.
- [ ] Write a sanitized note using `findings/TEMPLATE.md`: method, versions, anchors,
  confidence, failed checks and limitations. Keep raw exports private.

**Finish when:** the same private input and pinned dependencies reproduce a usable project,
and the anchor checks support the address/type mappings. Record addresses as `(build ID, RVA)`.

## 3. Establish a reproducible compiler worker

Issues: [#3 — Compiler worker](https://github.com/awarebayes/skyrim-research/issues/3),
[#4 — Boat experiment](https://github.com/awarebayes/skyrim-research/issues/4).
Prerequisite: step 1; evidence from step 2 helps identify compiler candidates.

- [ ] Investigate candidate Microsoft compiler generations/settings for the selected Skyrim
  build. Record evidence and alternatives; FNV's compiler is not a Skyrim toolchain decision.
- [ ] Select one host route: x64 Linux with Wine, Windows Arm VM, or an x64 Windows host.
  Read [the Boat feasibility findings](boat-build-worker.md) if considering Boat.
- [ ] Before spending money or installing a VM, agree on the machine, storage, maximum cost,
  stop/delete behavior and authorized inputs. Researching Boat did not provision it.
- [ ] Install a legitimately obtained candidate toolchain on the approved host. Record compiler
  binary hash/version, host and target architecture, SDK/library provenance and exact flags.
- [ ] Compile original synthetic C++ twice in clean output directories. Exercise arithmetic,
  simple field access, a call and a branch; store generated objects privately.
- [ ] Compare the relevant code sections and explain any nondeterministic metadata. Publish
  original fixtures/recipes and sanitized results, not compiler packages or generated binaries.

**Finish when:** a documented command reproducibly builds synthetic x64 functions with the
pinned compiler. This establishes a worker, not proof that it is Skyrim's original compiler.
If Wine fails, record that result before considering another host. Do not substitute a different
compiler and call original-compiler compatibility solved. Stop paid workers after the experiment.

## 4. Build the comparator and its failure tests

Issue: [#5 — Matching gate](https://github.com/awarebayes/skyrim-research/issues/5).
Prerequisite: step 3. All initial fixtures can be original synthetic inputs.

- [ ] Write down the comparison contract: function boundaries, code bytes, reference resolution,
  relocations, exception-related coverage and exclusions. Follow [verification](verification.md).
- [ ] Implement extraction from PE/COFF and resolution of synthetic calls/data references.
  Define how source symbols map to target RVAs; an object file alone lacks final placement.
- [ ] Test rejection of a changed byte, wrong call/data target, truncated function, wrong image,
  stale source/recipe, unsupported relocation and omitted exception-related code.
- [ ] Handle aliases/overlaps explicitly. Fail closed for unsupported cases; do not normalize
  away unknown differences or mask relocation bytes without checking their targets.
- [ ] Generate sanitized reports with source revision, target hash, compiler hash/flags,
  comparator version, function identity, coverage and result. Keep raw diagnostics local.
- [ ] Reproduce the checks independently. Implement report/source consistency checks for CI.

**Finish when:** synthetic positive and negative cases establish what the comparator checks,
and another host or agent can reproduce them. The public `matched` gate remains disabled until
the real comparison in step 5 is also reproduced and the gate change passes its own Reviewer pass
under the [acceptance rule](verification.md#acceptance-rule). A hand-authored success flag is
insufficient.

Status: the report/source consistency check (the match gate in `tools/check.py`, with the
Reviewer record) and its negative tests (`tests/test_match_gate.py`,
`tests/test_accept_function.py`) are implemented and run in CI. The first function's real
comparison is reproduced on more than one host. The gate change still needs its own Reviewer
pass before this step is finished.

## 5. Reconstruct and accept the first real function

Issue: [#6 — First function](https://github.com/awarebayes/skyrim-research/issues/6).
Prerequisites: steps 2, 3 and 4.

- [x] Select a short function with well-supported boundaries and few dependencies. Prefer
  engine code over unidentified middleware; record any uncertainty about origin.
- [x] Add its build ID, RVA, size, name origin, owner and finding path to the inventory as
  `mapped`. Do not define whole-game scope from this one selected function.
- [x] Analyze it locally and document the signature, used fields, references and uncertainties.
- [x] Reconstruct privately, compile with candidate settings, compare, and retain each result.
  Permission to use an AI agent does not by itself authorize uploading game-derived material.
- [ ] If it will not match, investigate types, ABI, compiler choice and optimization settings.
  Record a blocked experiment when appropriate; do not weaken the comparison to claim success.
  (Not needed for the first function: the first draft passed.)
- [x] Reproduce the real comparison on a second verifier host against the pinned source, recipe
  and image.
- [ ] Land the gate/schema change tying accepted reports to integrated source (Engineer, with the
  reproduction and negative tests from step 4, plus a separate Reviewer pass on the change).
- [ ] Have a fresh Reviewer subagent check the reconstructed source for plausibility, name
  origins and provenance; then integrate, rerun checks and verifier, and record it as `matched`
  with `tools/accept_function.py` under the [acceptance rule](verification.md#acceptance-rule). The maintainer is not asked to
  review the function; escalate only as that rule lists.

Status: `sse-steam-1-7-104` `0x73ad90` was accepted, then revoked when its unit gained a function
and the record format changed; it is re-confirmed and `mapped` again, awaiting a fresh Reviewer
pass with the second batch (`findings/first-function.md`, `reconstruction/README.md`). Publication: the maintainer has decided that reconstructed source is
published in this repository by engine area (`LEGAL.md`); this function's source is pushed with
its acceptance.

**Finish when:** one integrated function has a reproducible accepted report and public metadata
passes validation. Only then should the site display its first accepted match. A byte match
establishes the checked code result, not the correctness of an inferred function name.

## 6. Produce the first behavior result useful to Mudcrab

Issue: [#7 — Movement selection](https://github.com/awarebayes/skyrim-research/issues/7).
Prerequisites: step 2 and an explicitly scoped runtime experiment. This research can proceed
before matching is complete if a suitable original-game runtime is available.

- [ ] Start with one question: how is the movement type selected when a race link is absent?
- [ ] Define controlled inputs, measurements and competing hypotheses before observing results.
- [ ] Establish original-game launch, SKSE/plugin logging where needed and isolated test saves
  on the chosen host. Track VM-specific failures separately. Boat runtime compatibility is unproven.
- [ ] Collect repeatable observations. Keep code-path interpretation distinct from observations.
- [ ] Write `specs/` input/output rules, units, edge cases and original synthetic tests using
  `specs/TEMPLATE.md`. Declare all relevant source exposure and keep transfer status UNREVIEWED.
- [ ] Obtain the documented boundary review before sharing implementation-bearing findings with
  Mudcrab implementers. Do not automatically copy reconstructed code or specs into Mudcrab.

**Finish when:** a reviewed specification/test set answers a concrete question, or a documented
negative result narrows it. Behavior research does not increase byte-match counts.

## 7. Expand only after the pilot is reproducible

- [ ] Try a second small function from a different code path to test the pipeline's generality.
- [ ] Refine the shared declarations when evidence supports them; retain provenance and unknowns.
- [ ] Define a reviewed function inventory and exclusions before enabling scope percentages.
  The bootstrap validator intentionally requires `null` totals until that extension is reviewed.
- [ ] Keep functions, bytes, behavior validation and task completion as separate metrics.
- [ ] Add historical charts, contributor/model credit and cost records only from real accepted
  records, with metric definitions and dates. Git history remains the audit trail.
- [ ] If running multiple agents later, define claims, ownership, expiry and integration checks
  before dispatch. Each match must be rechecked after integration and pass Reviewer approval; run
  the sampling safeguard from [verification](verification.md#acceptance-rule). Private inputs stay
  isolated from untrusted public PR jobs.

**Finish when:** a second researcher can reproduce the pilot and new work uses the same evidence
contract. Full executable building is a separate future project, not part of this first milestone.

## Publication routine for each completed step

1. Update the relevant work item in `data/progress.json` and `updated_at`; add a milestone only
   for an actual result. Leave unrelated tasks planned. Record blockers instead of inventing success.
2. Inspect `git diff`, stage named public files and check:

```sh
python3 tools/check.py --staged
python3 tools/check.py
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
git diff --cached --check
```

3. Review staged content for provenance, private data and secrets, then commit and push (the
   integrating Engineer, or the orchestrator when run with a shell); reconstructed functions also
   need the acceptance rule in [verification](verification.md#acceptance-rule). No per-commit
   maintainer review. Keep raw outputs under `.local/`. GitHub Actions publishes the report.
4. Close an issue only when its acceptance criteria and public evidence are satisfied. A website
   deployment or passing infrastructure tests alone does not close a research task.

## Handoff prompt for Claude or another agent

```text
Work in the skyrim-research repository. Read AGENTS.md and its linked policies, then
follow docs/plan.md step [NUMBER], linked issue [ISSUE]. Inspect current state first;
do not assume previous steps passed. Finish only this step's scoped work. Keep private
inputs and raw outputs local, label uncertainty, and report evidence, checks, blockers
and the exact next action. Do not provision paid resources, install a VM, upload game-
derived inputs or transfer implementation into Mudcrab without existing authorization.
```

Your immediate next action: **step 0, then locate your legally obtained executable for step 1**.
