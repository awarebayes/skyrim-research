# Pipeline review: where the cost went, what to change, what is left to find

Build `sse-steam-1-7-104` (image SHA-256 `846efccf…f1402f`, re-hashed for this work). Continues
`docs/resource-guidelines.md` ("the guidelines"), `docs/ideas-next.md` ("ideas-next") and the
matching cookbook; nothing in them is repeated. Task `p8-friction-and-ideas`, claude-fable-5-2, one
host, not reviewed. Nothing here is implemented.

**Evidence labels.** *Measured* = counted here with original stdlib scripts, private under
`.local/experiments/pipeline-review/`: `extract.py`, `orch.py`, `table.py`, `boat.py` (usage,
tool calls, timestamps and briefs from 53 subagent transcripts and the orchestrator session,
taken while five agents were still running); `pogo.py`, `ltcg.py`, `slotcheck.py`, `pex.py`
(image and game-data counts). *Estimated* = arithmetic on measured numbers. "M" is millions of
cache-read tokens, counted per API message as in `docs/costs.md`.

## 1. Cost and friction findings

**Totals (measured).** 6 h 35 min from first commit to the snapshot. 385M cache-read, 9.6M
cache-write, 2.9M output tokens: Opus 83% of cache reads, Fable 10%, Sonnet 7%. `data/costs.json`
holds 183M, so the ledger is half stale, and it attributes 4,961 of 8,857 billed Boat seconds.
6 functions are `matched`; 31 more passed the comparator and are uncommitted; 6 of the 9
near-misses were closed in a worktree.

**By stage, all batches (measured, M):** tooling 103; tooling fix rounds after review 33 to 46;
orchestrator 33; preparation 34; near-miss triage 33; label fix-ups 30; confirmation 20 to 45
(two Engineers mixed it with tooling); drafting 22; research 19; integration 11; function review
5.8; tooling review 4.7. Drafting and function review, the only stages that need a model per
function, are 7% of the total.

**Per function, by batch (measured; M per function):**

| batch | functions | prep | draft | confirm | review | fix-ups | integration | sum |
|---|---|---|---|---|---|---|---|---|
| first | 1 accepted | 8.6 | 1.5 | 13.5 | 2.5 | 0 | 9.6 | 35.7 |
| second | 5 accepted | 3.0 | 0.58 | 4.9 (with lint fixes) | 0.10 | in confirm | in confirm | 8.6 |
| third | 31 pending | 0.32 | 0.56 | 0.21 to 0.63 | 0.09 | 0.97 | not done | 2.2 to 2.6 |

The ledger's 2.2M "direct" for the second batch is a share of the same runs. Triage adds 32.9M
for 6 recovered functions (5.5M each). The orchestrator's 33M is not allocated.

**Third-batch timeline (measured, UTC).** Prep 22:47 to 23:01; dispatch waited until 23:24;
eight Drafters 23:24 to 23:31 (40 functions, 32 passes, 78 unit attempts); confirmation waited
for a busy Engineer until 23:46 and ran to 00:16; two Reviewers 00:17 to 00:22 (15 approve, 17
reject); label fix-ups 00:23 to 00:44; uncommitted at 00:55. Drafting and review took 12 of
those 91 minutes; the other 87% was serial confirmation, fix-ups and waiting for a consistent
tree.

**Friction sources, ranked by tokens lost (measured unless marked):**

| # | source | tokens | wall-clock | machine starts |
|---|---|---|---|---|
| F1 | fixed context of `general-purpose` subagents: 39.6k tokens before the first tool call against 10.9k for the `reviewer` type (47 and 6 agents) | 28.7k x 2,285 messages = 66M (17%) | none | none |
| F2 | Engineers resumed above 150k context: three segments at 257k to 333k per message (227 messages, 64.5M) against 120k to 170k for fresh Engineers; three ran into compaction near 365k | 30M to 37M (estimate) | compaction pauses | none |
| F3 | label rejections: 17 of 32 reviews, 16 for labels only; one resumed Engineer, 117 messages, 12 attempts, 5 confirms | 30.1M, more than drafting the batch (17.4M) | 21 min | 5 or more |
| F4 | tooling review loops: gate 5 Reviewer passes and 4 fix rounds (13.3M, 21 min, four commits); lint 3 passes; comparator v2 2 passes so far, first fix round 13M | Reviewers 4.7M, fixes 33M to 46M | about 1.5 h in all | re-confirms |
| F5 | orchestrator as relay: 135 messages at 246k average, 462k peak; its context holds 311k characters of tool results, 278k of briefs, 94k of notifications, 46k of messages; it also ran 58 shell commands and 15 commits | 33.2M; about 17M above a 120k ceiling (estimate) | serial dispatch | none |
| F6 | one-commit coupling: a comparator bump re-confirmed every unit, a label fix in a shared header made approved functions stale, `check.py` fails tree-wide on one stale record | re-confirm rounds inside F3 and F4 | 31 functions uncommitted 84 min and counting | re-confirms |
| F7 | one fork per confirmed unit: 95 `confirm` invocations in the transcripts; counters read 48 of 75 per day and 25 of 25 per hour at 00:44 | none | the hourly limit stopped confirmation | binding limit |
| F8 | model-run preparation: 10.0M for 40 packs after the exporter existed | 0.25M to 0.32M per function | 14 min | none |
| F9 | near-misses needing outside knowledge: 9 of 40; the four units holding them used 62 of 78 unit attempts | 32.9M triage; about 8M of drafting (estimate) | 46 min | 26 attempts |

Corrections to what was assumed: the Reviewer is the cheap half of a tooling loop (4.7M
against 33M or more for the fixes); the binding Boat limit was the hourly one.

## 2. Process changes, ranked

**C1. Agent types with small tool lists (F1).** Root cause (the difference is measured, the
cause inferred): Drafters and Engineers are spawned as `general-purpose`, which carries every
tool and connector definition; the four-tool `reviewer` type starts 28.7k tokens lower. Change:
add `.claude/agents/drafter.md` (Sonnet; Read, Write, Edit, Bash) and `engineer.md` (Opus; plus
Grep, Glob) and spawn by type. Saving (estimate): 33% of drafting (5.7M of 17.4M in the third
batch), 17% overall. Measure: the next Drafter's first-message context is under 13k. Engineer.

**C2. No resume above 150k; fix rounds go to a fresh agent (F2, F3, F4).** Root cause: follow-ups
went to whoever held the context, and each of its messages re-read 250k to 330k. Orchestrator
rule: an agent whose last context exceeded 150k is not messaged again; the next step goes to a
new agent with the handoff and the findings file. Saving (estimate): 45% of resumed segments,
30M of this session. Measure: cache-read per message by segment; none above 180k.

**C3. Labels checked before the compile, never first by the Reviewer (F3).** Root cause: the
lint checked label syntax; label truth was first tested by an Opus Reviewer.
`tools/check_labels.py` now exists. Change: `attempt` refuses a pass while it reports an error;
the packet shows its output; a label-only finding with an unchanged code-section hash is fixed
forward (C5), not rejected. Saving: 16 of 17 rejections and the 30M round. Measure: label-only
rejections per batch, target 0 to 2. Engineer.

**C4. Tooling review in fewer rounds (F4).** Each round found a real hole, so find them before
the Reviewer does:

1. *Design note first:* 60 lines on what is compared, trusted and parsed; one Reviewer pass
   (about 0.5M) before any code. The gate's rounds ended only when its C lexer was replaced by a
   line scan and a restriction, which was a design decision.
2. *Gates do not parse C++.* They consume compiler output or refuse the input: the include
   closure comes from the pinned compiler's own include listing, bound into the record, with the
   line scan as a cross-check. Two sources that must agree replace one parser that must be right.
3. *Mutation harness as a standing test* (`tools/mutate_probe.py`, in `check.py`): on every
   accepted object file flip each compared byte class, retarget each relocation (local,
   external, unbound), truncate at each `.pdata` and funclet boundary, drop or duplicate each EH
   table entry. A mutation of compared content must be rejected; survivors are listed for the
   Reviewer. Both blocking holes of comparator v2 quoted in its fix brief (a data reference
   through an external symbol skipped silently; a candidate cut at a chained boundary) are in
   these classes.
4. *Probe corpus:* every Reviewer probe becomes a negative test in `tests/probes/`; no tooling
   change goes to review until the corpus passes.
5. *No silent skip:* each comparison step returns compared, rejected or not-applicable with a
   reason code; a missing value rejects. Fix rounds follow C2.

Saving (estimate): one or two Reviewer passes per change instead of three to five; fix rounds of
2M instead of 13M. Measure: passes per change; harness survivors against Reviewer-found holes.
Engineer for 2 to 5, orchestrator rule for 1.

**C5. Decouple commits without weakening `matched` (F6).**

- *States.* `mapped`, then `pending` (unit and record committed, two-host comparator pass, no
  approve; never counted as matched), then `matched` with its present meaning: record, sources,
  comparator version and review all current. Units land when `confirm` passes; an approval is a
  second, small commit.
- *Per-unit validation.* `check.py` verifies each unit on its own; a stale or failing unit is
  demoted to `pending` by a scripted command and no longer fails the tree. Hygiene, schema and
  orphan-record checks still do.
- *Symbol map.* Implemented: a record pinned to an earlier map version stays valid across
  additions that cannot have changed its result, proven by rebuilding that version from the
  current map (`tools/symbol_map.py`, `docs/verification.md` "Symbol map"). Adding entries no
  longer stales every record; changing one stales exactly the records whose version held it.
- *Comparator versions.* A comparator commit contains the reports regenerated by a scripted
  `reverify --all` in the Boat session (seconds per unit, no model); failures are demoted in the
  same commit; the tooling Reviewer checks that the regenerated set equals the matched set.
  Without Boat, records are marked `reverify-due` and `check.py` fails after 24 hours.
- *Header changes.* A record binds its include closure, so stand-in headers are split per class
  (N3). If a unit re-verifies with the same `candidate.code_section_sha256` and a script shows
  the function's own source text unchanged, the approval carries over and the Reviewer sees the
  header diff once per header. A changed hash means a full review.
- *One worktree per batch*, merged by script when its units validate, so Drafters' untracked
  files no longer sit in the checkout everyone commits from.

Saving: the 84 blocked minutes; one review per header instead of one per dependant (8 for the
Actor unit become 1). Measure: minutes from `confirm` pass to commit, target under 5. Engineer,
after decisions 1 and 2.

**C6. The function loop as a script; the orchestrator plans (F5, F8).** A workflow script (the
repository's multi-agent script capability) runs: plan, export packs, open a worktree, spawn
Drafters, session confirm, `check_labels`, build packets, spawn Reviewers, apply verdicts,
commit, ingest costs. Models appear only as Drafter and Reviewer. The orchestrator stops
relaying: Reviewers write `.local/reviews/<id>.json` and fix agents get the path; briefs are at
most 1,500 characters and name a task file and the card (the third-batch Drafter brief, 1,400
characters, is the model); it restarts from a handoff at 120k. Saving (estimate): 17M of
orchestration per session of this size, 0.3M of prep per function, the dispatch waits (23 and
15 minutes). Measure: orchestrator cache-read per accepted function, now 0.9M, target 0.1M.

**C7. Two-machine sessions (F7), being built.** Target: 2 starts per session against about 1.3
per function so far. Add: a rename or comment-only change whose code-section hash was already
reproduced on two hosts needs one host (decision 2). Measure: the starts counter per session.

**C8. Ledger from the script.** Ingest every transcript by segment at the end of each workflow
run, with Boat seconds from the session log; today it misses 52% of tokens and 44% of seconds.

Expected cost per accepted small function after C1 to C7 (estimate): draft 0.3 to 0.4M, review
0.09M, fix-ups under 0.1M, orchestration 0.1M, prep and confirm 0: about 0.6M against 2.2 to 2.6M.

## 3. New technical ideas, ranked

Returns are diminishing. None of these beats executing what the two earlier documents already
rank first; N1 and N2 are cheap enough to do anyway.

**N1. Settle the whole-program question in one Boat session before building anything.**
*Outcome:* refuted; cause unknown. `/GL` with `/LTCG` and a flag sweep left every measured
near-miss unchanged ([finding](../findings/whole-program-optimization.md)), so no link-mode
verifier is built. The untested hypotheses now are EH state removed after frame layout (a
`noexcept` or `throw()` helper whose throwing path folds away) and frame layout kept from dead
code (an address taken and then optimised out). The plan as written follows.
*Measured:* the POGO record's signature is `LTCG`; its text groups are `.text$mn` (22.1 MB),
`.text$x` (1.13 MB), `.text$di` (1.06 MB), `.text$yd` (0.57 MB), `.text$mn$00` (32 bytes) and
`.text` (33 KB). No cold or split group and no profile signature exist, so profile data shaped
no function and nothing is unmatchable for that reason. *Measured:* a caller-saved register read
after a direct call without being rewritten occurs at 942 of 333,279 call sites; 364 are the
stack-probe helper (which validates the detector), the other 578 lie in at most 811 callers. So
cross-call register use cannot locate the 68 whole-program objects, and the Rich header only
counts them. *Experiment (10 Boat minutes, synthetic sources):* (a) link three ordinary and two
`/GL` objects with a map file; if the generated code is contiguous, the lock functions
(`0xce3250`) and `0x237a20`, 11 MB apart, cannot both be whole-program code; (b) compile the
unchanged lock unit under 16 recipe variants (one second-batch unit already needed `/fp:fast`)
and under `/GL` with a link. *A link step needs:* a `/GL` object holds no machine code, so the
candidate becomes a linked DLL with a map file, the function is found by map symbol and compared
image to image: a new contract mode with its own review. *Risk:* such code depends on the other
objects (inlining, constant arguments), so one unit may never reproduce it; if (b) passes only
with the link, record those functions as blocked by cause: at most 2.8% of objects. *Yield:*
2 to 3 functions; mainly it stops triage spending 33M on a cause no source change can reach.

**N2. Upgrade placeholder virtuals and flag wrong signatures from the code.** *Measured* on
17,003 virtual-slot targets with one community declaration (class export of task
`p7-class-skeletons`, both community revisions as pinned): of 1,623 checked placeholder
declarations, 730 (45%) read an argument register they do not declare in their entry block, and
390 that are leaves leave a value in the result register. Of 10,294 declarations with real
names, 108 (1.0%) read an undeclared argument, 14 declared `void` return a value, and 2 declare
a result the code never produces. So real community signatures agree with the code 99% of the
time on these tests, and automatic detection of wrong names has a small yield (about 120
entries), but the placeholder upgrade is free: 1,120 "takes at least N arguments" or "returns a
value" facts for packs, the kind that made `0x2e5a60` a near-miss. *Spec:* add both tests to the
class export, emit `signature_hint` and `signature_conflict` per slot, print them in the pack.
*Test:* the hints agree with the 37 accepted declarations. Engineer, hours. Risk: arguments
first read after a branch are missed, so it is a lower bound.

**N3. Header library with machine-written verification marks (better form of guidelines 5).**
*Measured:* 12 unit headers hold 1,559 lines against 613 lines of function code; 66 stand-in
type declarations, 50 distinct, 13 types declared in two or three headers. *Mechanism:* one
header per class under `reconstruction/include/`; after every accepted function a script records
per member "exercised by" the accepted RVAs whose pack lists that displacement, and per class
the C4 size; unexercised members stay marked unverified. Drafters extend the shared header
instead of writing stand-ins; the per-class split is what C5 needs. *Test:* stand-in lines per
new function fall from 42 to under 10; attempts per pass fall. *Risk:* a shared header change
re-verifies many units: needs C5 and C7 first.

**N4. Typed native signatures from the game's own compiled scripts.** *Measured:* the script
archive holds 14,026 compiled scripts with 54,709 functions; 686 are native declarations, in 44
script types, with 680 typed parameters and typed returns. Joined to the registration table of
guidelines technique 6, each gives a licence-clean name and signature for a wrapper and usually
for the member function it calls. *Yield:* at most 1,400 functions, under 2% of scope.
*Experiment:* confirm the registration record layout on 20 entries, join by name, check arity
with N2's test. Low priority; do it when technique 6 is built.

**N5, N6 (small).** Add "functions per class not yet in the header library" as a second key to
the fan-in order, so a populous class's first function is drafted early (not measured). Headers
of the two other Creation Engine games: not recommended; layouts differ by engine version,
neither source is authorized, and N2 shows the SSE declarations are 99% consistent.

**Critical path of the existing plan:** land the 37 pending functions (C5) -> session confirm
(C7) -> class export with skeletons -> shared headers (N3) -> stamping -> fan-in ordered
drafting with the cookbook -> permuter. C1, C2 and C6 cut the cost of every step and take hours.

## 4. Operating procedure for the next 1,000 functions

| # | step | who |
|---|---|---|
| 1 | Pick a batch of 100 to 200 by cluster representative, fan-in and header gain; refuse classes failing C1 or C2 | script |
| 2 | Export packs with class skeleton, signature hints, exemplar unit, cookbook symptom list | script |
| 3 | Stamp cluster members of accepted patterns; they skip steps 4 and 5 | script |
| 4 | Draft per class unit in a batch worktree: `drafter` type, brief of 1,500 characters, attempt limit, several variants per compile | Sonnet |
| 5 | `check_labels` and lint must pass before a pass counts | script |
| 6 | One two-machine session confirms every unit; records written; units become `pending`; commit | script |
| 7 | Near-misses: permuter, then one fresh Engineer per cause class with the cookbook; stop on a register-only or frame-only difference and record the cause | script, then Opus |
| 8 | Reviewer packets per class; fresh `reviewer` per 10 to 20 functions; verdict JSON to a file | Opus |
| 9 | Apply verdicts: approve commits `matched`; label notes fixed forward under C5; code rejections return to step 4 once | script |
| 10 | Promote headers, write verification marks, regenerate index and site, ingest costs | script |
| 11 | Read the run's summary file, decide the next batch, report to the maintainer; restart at 120k | orchestrator (Fable) |
| 12 | Tooling changes: design note, harness and corpus, one review, fresh-agent fixes, `reverify --all` in the commit | Opus Engineer and Reviewer |

Budget (estimate, from section 2): 0.6M cache-read per drafted function, 2 to 4 machine starts
per batch.

## 5. Decisions for the maintainer

1. **`pending` state and per-unit validation (C5).** Allow units with a two-host comparator pass
   and no approval to be committed and shown separately, and let a stale unit be demoted instead
   of failing the tree?
2. **Approval and reproduction carry-over on an unchanged code-section hash (C5, C7).** When a
   header or label change leaves `candidate.code_section_sha256` and the function's own source
   unchanged: is one host enough, and may the earlier approval stand with the header diff
   reviewed once?
3. **Blocked-by-cause status (N1).** If the experiment shows whole-program code generation,
   record those functions as blocked rather than build a link-mode comparator now?
4. **Main session as orchestrator.** The session that dispatched this work also ran commands and
   committed, which `AGENTS.md` assigns to workers. Either start it as `--agent orchestrator` and
   let the workflow script commit, or change the rule to match practice.
