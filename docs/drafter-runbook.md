# Drafter runbook (queue sessions)

Paste into a fresh session, with your own worker label (and the profile, if not `cheap`):
`Read docs/drafter-runbook.md in this repository and follow it exactly. Your worker label is <label>.`

A brief from `python3 tools/flow.py brief drafter` may name a profile and a queue directory; then
pass `--profile <profile>` and `--queue-dir <dir>` to every `work_queue.py` call below.

You are a Drafter. Goal: take small C++ units from the shared queue one at a time and write source
that compiles to the same bytes as the game, until the queue is empty.

## Five binding rules

These are the rules of `AGENTS.md` that apply to you, already distilled. Its "First read" list and
every other document are optional: an unread document is never a reason to stop.

1. **Private stays private.** Everything under `.local/` (sheets, listings, decompiler output) is
   game-derived. Read it; never copy its text into a source file, a comment or any message. Write
   your own C++.
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

0. Read `docs/drafter-card-small.md` once (91 lines). Its "Rules" and "Result lines" tables are the
   fixes you will need. Ignore its step 1 (skeletons already exist) and its handoff section (step 9
   here replaces it).
1. `python3 tools/work_queue.py next --worker <label> --profile cheap` prints a unit dir, e.g.
   `.local/tasks/q1-s02-niobject/q1-s02-niobject-bsxflags`. If it prints `EMPTY`, go to "Finished".
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
9. Report and release the unit, one `--result` per function and one for the unit:
   ```
   python3 tools/work_queue.py done <unit dir> \
     --result '{"rva": "0x4aa860", "result": "pass", "reason": "all-checks-passed", "attempts": 2}' \
     --result '{"unit": "reconstruction/bsengine/X.cpp", "attempts": 2, "blocker": null, "friction": null}'
   ```
   `result` is `pass` only if the last attempt printed PASS for that RVA. `blocker` names the
   near-miss file or the problem; `friction` is one sentence on anything that slowed you, or null.
10. Go to step 1.

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
