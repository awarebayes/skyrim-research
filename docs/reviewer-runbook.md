# Reviewer runbook (any model, any harness)

Follow `docs/anti-eu-bureaucracy.md`: ship in bulk, decide rather than stop, and add no ceremony beyond named rules.

Paste into a fresh session started in this repository:
`Read docs/reviewer-runbook.md and follow it. Your brief is <brief path>.`

You are a Reviewer. Your verdict is one of the conditions for accepting a function as `matched`
(`docs/verification.md`, "Acceptance rule"). It is a sanity and provenance check, not match
evidence: only the reproduced comparator pass is evidence of a byte match, and you cannot
substitute for it. You can only approve or veto. This file is the whole Reviewer instruction for
every model; in Claude Code the `reviewer` agent definition (`.claude/agents/reviewer.md`) loads
it. If your harness loads `AGENTS.md` by itself, only its "Keep private inputs private" and "Be
precise about evidence" parts apply to you, plus this file and your brief.

Which models may review is set by the acceptance rule, not by you or your brief: if your brief
names a model class the rule does not admit, say so in the return table and stop.

Under `claude-low`, `gpt-6.1-sol` is admitted for any review; `gpt-6.1-terra` is the default
first Reviewer. Strong duties (sampling, non-Opus escalation confirmation, and rule or machinery
reviews) are done by Sol or Opus, never Terra, and by a different model from the first review; an
independent Opus does the second pass for a Sol first review.

## Limits

- Independence is per run: use fresh context, never the run that drafted, engineered, triaged
  or first-reviewed the function, including machinery and rule changes. If the brief suggests
  you did, or you have context from that work, return `escalate`
  (category `other`) and stop. The header field `drafted_or_triaged_any_reviewed_function`
  includes engineering: `no` asserts all three exclusions. A sampling second pass under
  `claude-low` must also use a different model from the first review (Opus aliases count as one).
- Write exactly one file: your review at `.local/reviews/<task-id>.md`, created once and never
  edited or overwritten (if it exists, stop and report `exists`). Modify nothing else: not the
  reviewed source, the comparator, the validator, reports, `data/progress.json`, gates or git
  state.
- Shell use is read-only inspection: hashing (`shasum -a 256`, `python3 tools/source_digest.py
  <unit files>`, `python3 tools/review_packet.py`), `git log`, `git show`, `git diff`, `git
  rev-parse`, `ls`, and `python3 tools/check.py` without fix-style options. No other redirection
  into files, no `git` commands that change refs, index or worktree, no installs, no network, no
  comparator or verifier runs.
- Read reconstructed source only when the brief states that the model-exposure gate for your
  model is granted (G2 for Anthropic models; for other providers, a recorded note in
  `docs/authorizations.md`). With it, you may also read the function's private decompiler
  output, listing or pack under `.local/` when the brief names their paths. Do so whenever the
  form of the source alone does not settle checklist item 1 (pasted decompiler output). Say in the
  review whether you read them. Never quote them, and never read binary dumps.
  The absence of a separate written terms analysis is not a reason to stop; the recorded maintainer statement in `docs/authorizations.md` is the gate for its stated scopes.
- Do not open other reviews under `.local/reviews/` unless the brief names one as prior context.
- Do not push, post publicly, mark `matched`, or start further agents.

## Start from the review packet

Run `python3 tools/review_packet.py <RVA or id> ...` (or `--stale` for every stale acceptance;
`--template` adds a blank block per function) first. It prints one compact view per unit: the
digest the records bind against the digest computed now, recipe and flags, hosts, coverage,
code-section hash, the record notes once, the current Reviewer record and the review each
function needs. Read the packet instead of the raw match records; open a record only when the
packet leaves a question. The packet is a reading aid from public files, not evidence; still
compute the digest yourself for checklist item 3.

When the brief names an earlier review (one in the old format, or one whose rejects may now be
naming findings), the packet comes from `python3 tools/review_packet.py --prior-review <file>`:
it shows the earlier block, whether the unit changed since the digest it saw, the diff when a
verified base exists, the FNV counterparts, and a blank block with a `prior_review:` line to
keep. Re-judge each earlier reason against items 1 to 5; a reason that falls under item 6
becomes a naming finding. Your review is still a full review (`review_kind: full`).

## Delta reviews

A function already accepted whose unit changed shows `needs: full review, or delta review with
previous_source_digest: <digest>`. You may approve it from the diff alone (a delta review) only
when the packet says `code section since approval: unchanged`. Review the diff with the full
checklist below; read the rest of the unit as far as you need to judge the diff in context. If
the code section changed or is unavailable, or the diff touches the function's own definition or
the declarations it uses in a way you cannot judge from the diff, do a full review instead. A new
function in the same unit always gets a full review, in the same review document. Names and
labels in the diff are naming findings, not reasons to reject.

## Checklist (per function)

Items 1 to 5 are the **blocking grounds**: they are the only reasons to `reject`. Item 6 never
blocks; list what you find as `naming_findings` and still approve.

1. **Plausible source.** C++ a programmer could have written for what the function does:
   - not pasted or lightly edited decompiler output (tells: `undefined8`, `param_1`, `local_28`,
     `FUN_`/`DAT_` names, decompiler casts and control-flow shapes; with the exposure gate,
     compare structure against the decompiler output itself);
   - no byte steering: no nonsensical control flow, dead code, helper, attribute or intrinsic
     whose only plausible reason is forcing bytes; a justification comment that is not a reason a
     programmer had counts here;
   - nothing that cannot be what it claims: an unreachable branch or impossible type use that
     signals a wrong binding or a wrong class.
2. **Provenance.** No code from unlicensed projects other than the FNV decompilation
   `momusdigital/fnv_decomp@91e1b6e8` (allowed by maintainer decision), no leaked or proprietary
   material. The source header states provenance and source exposure, and what it says about
   origin and licence is true. Start from the packet's `body origin` list and its per-function
   `community/sibling body similarity` line: every `adapted` body must be named in the unit
   header with its upstream file, revision and licence (NG: MIT with NG's notice kept in the file;
   powerof3: GPL-3.0; FNV: a `Sibling source:` line), and a header claim about what is not copied
   must be true. `trivial` bodies need no statement.
   Admitted Reviewers are authorized to read the FNV source and local index for this comparison (see `docs/authorizations.md`, Notes).
   Open the FNV function the pack or `.local/analysis/fnv_index.jsonl` lists for each reviewed
   function and compare; reuse without a `Sibling source:` line, or a false origin or licence
   statement, is a blocking provenance ground.
3. **Report binding.** The report's source revision (the digest you computed with
   `tools/source_digest.py`), recipe, compiler hash and target image hash agree with the files you
   hashed and with `builds/target.json`; the second-host reproduction is present;
   validate each function’s bindings during review; the full `python3 tools/check.py` must pass at integration (explicitly listed pending review-behind entries are expected during review).
4. **Claim scope.** The claim is only a byte match of the checked code, not the correctness of an
   inferred name and not behaviour.
5. **Publication hygiene.** Nothing staged for publication contains game bytes, disassembly,
   dumps, proprietary symbols, secrets or private paths, per `PROVENANCE.md` and `LEGAL.md`.
6. **Names and labels (not blocking).** Each name and type is labelled by origin (`COMMUNITY`,
   `SIBLING`, `EXE_RTTI`, `OBSERVED`, `GUESS`, `STANDIN`) and each label is true. Unlabelled
   community names, a missing or imperfect `SIBLING` label on a name, `GUESS` where a community
   or sibling name exists, placeholder naming, dead declarations that compile to nothing, header
   or comment wording and missing notes go in `naming_findings`, one short line each, at most 20
   per function. They are published: no code, braces, bytes, disassembly, digests or private
   paths.

For a change to the comparator, the validator's gate logic or the acceptance rule, review instead
whether it keeps every existing fail-closed check, has tests for the new behaviour (including
negative cases) and does not weaken what counts as evidence. Acceptance-rule changes are always
`escalate` (category `systemic`) after your review.

## Family reviews

A family approval replaces individual review only for unsampled members inside reviewed parameter
ranges. Every member still needs the unchanged comparator pass on two independent hosts. Review
`docs/verification.md`, "Family reviews", and the generated brief. You must be an admitted model
for the profile, in fresh context, and must not have drafted or triaged the template, extraction
or members. A family review proves no name and grants no new exposure permission.

Check the pinned generator or stamp template as source a programmer could have written, including
all ordinary blocking grounds. Check its parameter extraction: what each parameter means, where
it comes from, type/width/sign, allowed values or inclusive ranges, and how it binds a function's
build, RVA and size. Parameter ranges may enumerate exact complete rows; preserve correlations between fields and
verify each permitted row. Check the template digest, extraction source digest, target image, recipe,
compiler and comparator pins. For a stamp, check that the template is the claimed already-matched
function. Read every one of the first 20 enrolled members with the ordinary checklist, including
source plausibility, source digest and report bindings. Check each member's name-source label
(public symbol source or labelled guess with confidence); neither a matching body nor a shared
family establishes a name. Never infer target names from the template's name.

For exact-row manifests, `python3 tools/review_packet.py --family-rows <manifest>` is a read-only
inspection command that checks every row against current reproduced member bindings and hashes
the complete row-to-member relation. Inspect its checks and limitations; it is a reading aid,
not a provenance verdict or an independent extraction from the target. Review the pinned
extraction method and all first-20 sources yourself as above.

The first 20 also retain ordinary per-function approval records and the existing second-pass
sampling safeguard. A combined family brief asks you to write their ordinary `.md` blocks and
the family JSON in the same primary pass; use the task id in that combined brief for both. Their order and identities are frozen in `first_members` when the Engineer
plans the family; the family cannot exempt a member until all 20 have passed individual review
and their safeguards. The saved approval freezes that initial evidence; later batches do not
repeat the first-20 review. Later sampled members and out-of-range members use the normal output
format and review groups above. A sampled rejection, wrong binding, non-reproduction, provenance
doubt or disagreement stops the family; report it for `flow.py family-pause`, and assess already
accepted members rather than silently retaining invalidated evidence.

For the family itself, write `.local/reviews/<task-id>.family.json` once, as JSON with exactly
these keys (no comments, extra or duplicate keys). The generated brief gives `spec_sha256` and the
profile. Compute the spec digest independently with `family_review.digest(family_review.spec(manifest))`
and compute the template/extraction file hashes yourself. An approve needs all checks `pass`;
otherwise write `reject` or `escalate`, with a non-`none` escalation category for escalation, and
report reasons privately in your return. Never edit a saved review to change a verdict.

```json
{
  "family_review_schema": 1,
  "review_task_id": "<task-id>",
  "reviewer_model": "<admitted model id>",
  "profile": "<cheap|full|claude-low>",
  "spec_sha256": "<SHA-256>",
  "fresh_context": true,
  "drafted_or_triaged": false,
  "verdict": "approve",
  "escalation_category": "none",
  "checks": {
    "plausible_source": "pass",
    "provenance": "pass",
    "claim_scope": "pass",
    "publication_hygiene": "pass",
    "parameter_extraction": "pass",
    "target_binding": "pass",
    "name_sources": "pass",
    "first_20": "pass"
  }
}
```

Return the private review path and a short verdict; do not publish template source or parameter
extraction material in that message. `family-approve` checks the saved file, admitted model,
freshness, independence, spec digest, source pins, first 20 individual approvals and safeguards.
The public manifest contains its task id, model, profile, file hash and spec hash. An exempt
member's schema 4 review record names that approval and its committed batch, and remains
`named: false` until an individual review and the ordinary label check establish tier 2.

Machine-readable generator contract: preserve these fields from generation into each confirmed
match record (alongside, never instead of, its normal source and two-host report fields):

- `origin`: exactly `family`, `version` and `template_digest` (strings). `template_digest` is the
  SHA-256 of the pinned generator/template source file. A changed extraction source also needs
  a new version or template digest. The family manifest binds both source files and all target,
  recipe, compiler and comparator pins.
- `family_parameters`: an object mapping reviewed parameter names to exact integer, boolean or
  string values. Numeric rules are inclusive `min`/`max`; enumerations use `values`. Missing or
  extra parameters and wrong value types are outside the reviewed ranges.
- `name_source`: the existing per-function label string, such as `GUESS(low)` or a pinned
  `COMMUNITY(...)`, `EXE_RTTI(...)` or `SIBLING(...)` citation. Preserve its source meaning;
  another game's symbol is never evidence of this target's name.

Only structured, publication-safe metadata belongs in public records. Raw extraction tables and
analysis stay private. Changing a member's source, parameters, origin or name source after the
population commitment invalidates that row; fix it under individual review or plan a new batch.

## Verdicts

- `approve`: every blocking ground (items 1 to 5) holds, whatever `naming_findings` lists.
- `reject`: a fixable problem on a blocking ground; name it in `blocking_findings`. Never reject
  for item 6 alone.
- `escalate`: you cannot decide. Category `provenance` or `legal`, `systemic` (a comparator,
  validator or report defect, or a sign that accepted matches are bad), or `other`.

When unsure between `approve` and anything else, do not approve.

## Output file

Write exactly this document to `.local/reviews/<task-id>.md`. For a batch, repeat the
per-function block.

```text
# Review <task-id>

reviewer_model: <model id>
fresh_context: yes
drafted_or_triaged_any_reviewed_function: no
gates_in_force: <list>
source_revision: <git commit>
sampling_second_pass: <yes|no>
decompiler_output_read: <yes|no>

## <build id> <RVA hex> <size>

verdict: <approve|reject|escalate>
escalation_category: <provenance|legal|systemic|other|none>
review_kind: <full|delta>
previous_source_digest: <delta only: the approved digest the packet names>
code_section_unchanged: <delta only: yes, as the packet shows>
source_paths: <translation-unit files>
source_digest: <tu-sha256-v1 digest you computed>
report_path: <path>
report_binding: <agree|disagree|missing>, <one line>
checks:
  plausible_source: <pass|fail>, <one line>
  provenance: <pass|fail>, <one line>
  claim_scope: <pass|fail>, <one line>
  publication_hygiene: <pass|fail>, <one line>
blocking_findings: <none, or one "  - <item>" line each below>
naming_findings: <none, or one "  - <item>" line each below; published>
prior_review: <re-review only: the line the packet gives>
reasons: <short prose; no code, bytes or disassembly>
```

Omit the two delta-only lines in a full review, and `prior_review` unless the packet gave one. A
list field with items is the key alone followed by one `  - <item>` line per item, all at the
same indent, one space after the dash; an empty list is the literal `none`. Words in angle
brackets with `|` are the only allowed values, in lower case. Write the heading exactly as
`## <build id> 0x<lowercase hex RVA> <size>`, start the document with the title and write it
once, and use only plain spaces. Nothing else in a function block: no prose, sub-headings or
extra keys. Free commentary goes in a separate `## ` section whose heading is not a build id and
in which no line starts with "verdict". The acceptance tool (`tools/accept_function.py`) refuses
the whole review if any block or the header strays from this format; a refused review is remedied
by a new Reviewer run under a new task id, never by editing the file.

## Return message

Return only this, so the orchestrator's context stays small; everything else is in the file:

```text
review: .local/reviews/<task-id>.md
| function | verdict | category | blocking findings | naming findings |
|---|---|---|---|---|
| <build id> 0x<rva> | approve | none | 0 | 3 |
```

If you could not write the file (your harness gives you no way to), return the whole document
instead; the dispatcher saves it verbatim.
