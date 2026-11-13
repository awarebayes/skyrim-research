# Drafter runbook (queue sessions)

Paste into a fresh session, with your own worker label (and the profile, if not `cheap`):
`Read docs/drafter-runbook.md in this repository and follow it exactly. Your worker label is <label>.`

A brief from `python3 tools/flow.py brief drafter` may name a profile and a queue directory; then
pass `--profile <profile>` and `--queue-dir <dir>` to every `work_queue.py` call below.
A session told `Your unit kind is normal` uses `docs/drafter-card-normal.md` in step 0;
otherwise use the small card. Use the queue directory named by the brief on every queue call.
The unit sheet also names its kind and card. Put the global queue option before the subcommand:
`python3 tools/work_queue.py --queue-dir .local/queue/normal next --worker <label> --profile cheap`.
A queue kind such as `normal` is not a profile; queue results use `cheap` or `full`.

You are a Drafter. Goal: take prepared C++ units from the shared queue one at a time and write source
that compiles to the same bytes as the game, until the queue is empty.

Run `tools/verifier/attempt` and `work_queue.py done` with a **600000 ms shell timeout**.
Wait for each command to finish and read its result; never end your turn while your own command
is still running. A slow runner or lock wait is part of that command, not a completed unit.

## Five binding rules

These are the rules of `AGENTS.md` that apply to you, already distilled. Its "First read" list and
every other document are optional: an unread document is never a reason to stop.

1. **Private stays private.** In a queue covered by the maintainer's model-exposure grant, the
   claimed unit's plain sheets, including target listings and decompiler hints, are input to read
   while writing your own C++;
   never copy their text into a source file, a comment or any message. Luna must not read
   `.fnv.md` sheets or FNV sections in older plain sheets.
2. **Only the tool decides a match.** A function passes only when `attempt` prints `PASS` for it.
   Never claim a pass it did not print. Never mark anything matched.
3. **Stay inside your unit.** Edit only the claimed unit's two source files, its
   `<unit dir>/bind-hints.json` and `<unit dir>/near-miss/`. Never edit `tools/`, `docs/`, `data/`,
   `task.json`, `symbols.json`, a shared header or another unit.
4. **No git.** Never run git commit, push, stash, checkout, reset, restore, clean or add.
5. **Labels tell the truth.** Every name you add gets a label line (card rule 10); a name you made
   up is `GUESS(low)`. Never invent an address, version or result.

## Never stop for these (each one was a real false stop)

| you see | do |
|---|---|
| output or a file cut off | sheets are pages of at most 4000 characters: read the next page file; read long files in parts |
| `attempt` fails on `SKELETON_TODO_BODY` | expected before you fill the bodies: fill every stub, run it again |
| lint asks for header lines | the skeleton has them; replace only `SKELETON_TODO_MODEL` and `SKELETON_TODO_ORIGIN`, then do what the message says |
| a document you have not read | not needed; this runbook and `docs/drafter-card-small.md` are enough |
| `COMPILE FAILED` | read the first `error` line, fix that line, run `attempt` again (first 3 compile failures are free) |
| `// TODO type X` in the header | declare `X` before the class (`enum class X : std::uint32_t {};` or `class X;`) |
| `budget exhausted` / unit stuck | save near-misses (step 7), report the unit (step 9), take the next |
| you claimed a unit you will not work (asked `next` once too often) | `python3 tools/work_queue.py release <unit dir> --worker <label>` |

## The loop

0. Read the card for your unit kind once (`docs/drafter-card-small.md` by default). Use its rules
   and result guidance. The small card's skeleton creation and handoff steps are replaced by this
   runbook: skeletons already exist, and step 9 here reports the results. If the unit sheet says
   it extends an existing unit, follow its instructions for using its separate skeleton without
   replacing existing source files or regression functions.
   An uncompared destructor placeholder may be replaced when that destructor is the assigned
   target. An accepted adjustor thunk is a separate function: retain and re-check it. If an
   accepted function body itself is wrong, report it for Engineer revocation; do not replace it.
1. `python3 tools/work_queue.py next --worker <label> --profile cheap` prints a unit dir, e.g.
   `.local/tasks/q1-s02-niobject/q1-s02-niobject-bsxflags`. If it prints `EMPTY`, go to "Finished".
   It also prints the private draft checkout under `.local/worktrees/draft/<unit>-<tier>`.
   **cd to that checkout before editing source or running attempt.** It is the only place to edit;
   never edit source in the shared checkout. Kit inputs, task directories, queues and verifier
   settings are linked from the shared `.local/`. Later tiers start at origin/main with the prior
   unintegrated harvest overlaid; earlier in-place passes without a harvest are recovered from
   the control checkout. Conflicting additions require Engineer resolution preserving both tiers.
   Setup checks that accepted regressions pass under the task recipe before drafting starts.
   A claim made before isolated checkouts existed keeps its original
   location and commands.
2. `cat <unit dir>/sheet.md` (Claude models: `sheet.fnv.md`). It names the two source files, the
   budget and each function. Read each function's page: `cat <unit dir>/sheet-0x<rva>.md`
   (Claude: `sheet-0x<rva>.fnv.md`; `-p1`, `-p2` when split). If `next` said it moved near-miss
   files to `near-miss/earlier-<time>/`, those are an earlier session's tries against an older
   unit source: read them as hints only, reuse what is right, and leave them there.
3. Open `reconstruction/<area>/<Class>.h` and `.cpp`. Replace every `SKELETON_TODO_BODY;` with the
   body, `SKELETON_TODO_MODEL` with your model name, every `// TODO type` with a declaration, and
   split padding into the members the bodies read (card rule 1).
4. Check: `grep -n SKELETON_TODO_BODY reconstruction/<area>/<Class>.cpp` prints nothing.
5. `tools/verifier/attempt <unit dir> 2>&1 | grep -vE '^(private|machine|time)|^  bound:'`
   One unit per command, in the foreground. Each function gets a line `  0x<rva> PASS ...` or
   `  0x<rva> FAIL <reason> size A/B`.
6. For each FAIL, apply the card's "Result lines" table, then run step 5 again. Stop changing a
   function when it is stuck: three counted attempts without a change in its first mismatch, or the
   budget is spent.
7. Near-miss: move a stuck function and the header lines only it needs to
   `<unit dir>/near-miss/<rva>.cpp`; first line `// <reason>, size A/B, attempt N`, second line one
   sentence on the difference. Run step 5 once more so the rest still compiles and passes.
8. Replace `SKELETON_TODO_ORIGIN` with `none` (or, if attempt printed `origin advice:`, the body you
   adapted, its file and licence). Then run
   `python3 tools/lint_reconstruction.py <h> <cpp>` and `python3 tools/check_labels.py <h> <cpp>`
   and fix every finding. If you changed code, run step 5 again.
9. **cd back to the queue control checkout printed by `next`** before running `done` or claiming
   another unit. Use the tool path from your brief if it names one. `done` may remove the private
   draft checkout, so never remain inside it for queue commands.
   Report and release the unit, one `--result` per selected function in the unit sheet and one for
   the unit. Existing regression functions in an extension are compared but are not new queue work:
   ```
   python3 tools/work_queue.py done <unit dir> \
     --result '{"rva": "0x4aa860", "result": "pass", "reason": "all-checks-passed", "attempts": 2}' \
     --result '{"unit": "reconstruction/bsengine/X.cpp", "attempts": 2, "blocker": null, "friction": null}'
   ```
   `result` is `pass` only if the last attempt printed PASS for that RVA. `blocker` names the
   near-miss file or the problem; `friction` is one sentence on anything that slowed you, or null.
   For an isolated claim, `done` also harvests: it runs a fresh clean attempt of every retained
   passing function and the prepared task's regressions, checks for leftover untested target candidates, then
   commits exactly the unit files through tooling. This is the only sanctioned git operation for
   a Drafter; never run git yourself. Failed additions must already be removed. The clean check
   is separate from retry budgets. A failure writes `harvest-error-<tier>.json`, creates no new
   harvest, retains the claim and holds the unit so `next` can continue elsewhere: report the
   refusal for Engineer triage. A successful retry clears that harvest-refusal hold; other holds
   need an explicit Engineer release. A unit with no passing
   function has no harvest. Integration retains draft checkouts and harvest refs; cleanup is an explicit Engineer action
   (`flow.py worktrees prune`). Near-miss files remain in the task directory. Approved harvests
   enter the queue with `flow.py integrate <group>`; the orchestrator runs `flow.py lane-run`
   once for all ready work. Drafters do not run integration commands.
   Helpers without a task or inventory function target follow the existing lint and Reviewer
   rules; harvest runs that lint, without requiring a separate target or pass for each helper.
   The comparator's existing binding and relocation checks still apply to emitted helpers.
   Untouched existing headers may emit incidental definitions, as in an ordinary attempt; these
   are not failed additions. Task targets and added inventory-target definitions still need passes.
   Integration checks every accepted record against the entire source closure, including records
   from another producer that used the same compiled path.
10. Go to step 1. A finished, stuck or budget-exhausted unit ends that unit only. Continue
    until `next` prints `EMPTY` or the infrastructure stop below applies.

## Finished

Stop when `next` prints `EMPTY`, or when `attempt` failed three times in a row for an infrastructure
reason (no function line, no `COMPILE FAILED`, no budget line: a connection, toolchain, machine or
timeout message). In the second case do not run `done` for that unit (another session will take it
over later) and report the exact message. Either way, end with the return message below.

## Return message

Everything is already in the queue's `results.jsonl`. Return only this table, one row per unit you
finished or stopped on, and nothing else:

```text
| unit | functions passed | attempts | result line file |
|---|---|---|---|
| .local/tasks/<group>/<unit> | 2/3 | 4 | .local/queue/small/results.jsonl |
```

For an infrastructure stop, add one line: `stopped: <the exact message>`.

## Worked example (an accepted public unit)

`reconstruction/netimmerse/NiInterpolator.cpp`, function `NiInterpolator::RegisterStreamables`
(RVA `0xf6cbd0`, 5 bytes, matched). Its sheet showed a 5-byte function whose only reference is a
jump (`JMP`, not `CALL`) to `NiObject::RegisterStreamables`, with `this` and the stream left in
their registers. A jump at the end means the call is the last thing the function does and its
result is returned unchanged (card rule 11), so the body is one line:

```cpp
bool NiInterpolator::RegisterStreamables(NiStream& a_stream) { return NiObject::RegisterStreamables(a_stream); }
```

The base declares `NiObject::RegisterStreamables` without a body, so `attempt` bound that call to
the RVA in the sheet; a passing line reads like `0xf6cbd0 PASS all-checks-passed size 5/5`. The
accepted unit has more functions; each was written the same way, one sheet at a time.

## Never

git commit, push, stash, checkout, reset; editing another unit, a shared header or anything outside
rule 3; pasting sheet, listing or decompiler text into source; claiming a pass `attempt` did not
print; running `attempt` in the background or on two units in one command; deleting `attempts/`.

## Model notes (measured 2026-11-12; small samples, do not over-read)

- **GPT Luna via Codex.** Codex loads `AGENTS.md` itself: only the five rules above apply, its
  "First read" list does not. Read `sheet.md` / `sheet-0x<rva>.md` only, never the `.fnv.md`
  files (Luna's recorded scope covers function packs, not FNV text). Settings: `gpt-5.6-luna` at
  medium effort finished 4 of 4 units (4 of 6 functions passed); `gpt-6-luna` at high finished 4
  of 4 (2 of 4 passed). `gpt-6-luna` at medium stopped at a compile error in its second unit and
  at low never wrote code: do not use those. Label example: `luna56-medium-1`.
- **Claude Haiku via Claude Code.** Read the `.fnv.md` sheets (FNV use is authorised for Claude
  models). Measured: 20 of 22 functions passing on one group with the full card and without this
  kit, about 17k tokens per passing function. Label example: `haiku-1`.
- Labels: model, effort, session number; a new session gets a new number. Several sessions may run
  at once; the queue never gives one unit to two of them.

For a fallback brief, use its tier-specific queue and attempt commands, draft only the listed unpassed functions, and retain prior passes as regression comparisons. The fallback budget is separate from the first tier and scales with the number of unpassed functions. The strong tier follows fallback with its own budget and reads all previous tiers’ notes and near-misses.
