# Drafter card

Everything a Drafter needs. Do not read AGENTS.md or other policy documents; the tools enforce them.
Gates: G1 to G5 granted; private inputs and outputs stay under `.local/` and are never pasted anywhere.

**You get** a context pack (function notes, community types) in your brief and a private task
directory `.local/tasks/<task-id>/` with `task.json` (build id, RVA, size, symbol, compiled file,
recipe, attempt budget) and the symbol map. You work in your own git worktree.

**The loop.** Write or edit `reconstruction/<area>/<Class>.h` and `.cpp` in your worktree, then run
`tools/verifier/attempt .local/tasks/<task-id>` from the worktree root (about 10 s when warm).
It prints one line per function: PASS/FAIL, reason code, first mismatch offset, candidate/target
size. Read locally `attempts/<NNN>/0x<rva>/side-by-side.txt` (target vs candidate disassembly,
`*` marks differing rows) and `compile.log`, revise, repeat. When finished run
`tools/verifier/attempt --stop`.

**Source rules** (`python3 tools/check.py` runs the lint; a Reviewer rejects the rest):
- Plausible C++ for what the function does. No inline asm, `__emit`, byte arrays or `\x` strings,
  `__pragma`/`_Pragma`, `#pragma` other than `once`/`pack`/`warning`, or
  `__declspec(naked|code_seg|allocate|safebuffers)`. No dead code or odd control flow only to
  force bytes; justify anything unusual in a comment.
- One class per `reconstruction/<area>/<Class>.{h,cpp}` (lowercase area, `misc/` if unsure); the
  .cpp includes its header as `#include "<Class>.h"`.
- Include lines are exactly `#include "path"` or `#include <system>` with nothing else on the line;
  never `#` and `include` together in a comment or string; no include inside `/* */` or `#if`
  (header guard aside); repository headers quoted. `attempt` refuses a unit whose compiler include
  list differs from the derived closure.
- Header comment of each file: build id and `Source exposure: <black-box|community-headers|binary-analysis|mixed>`.
  The .cpp adds `RVA 0x<rva>` and `<n> bytes` per compared function, `Evidence: <findings/ or reports/ path>`,
  `Drafted by <model>`, `Recipe: reconstruction/recipes/<name>.json` and which functions are compared.
  The .h labels each name `COMMUNITY` (repository, revision, licence) or `GUESS`.
- No decompiler output pasted as source, no code from unlicensed projects (FNV repositories),
  nothing leaked. Unknowns stay unknown (`unk28`), not invented names.

**Budget.** `attempt` refuses past `max_attempts` (exit 5); stop early after three attempts with no
progress on the first mismatch offset. **Never** edit tools/, reports/, data/, recipes or another
unit, mark anything `matched`, commit, push, post, start agents or drive Boat by hand.

**At the end** write JSON lines only, one per function and one for the task, to
`.local/handoffs/<task-id>.jsonl`, and return the same lines:

```json
{"rva": "0x73ad90", "result": "pass", "reason": "all-checks-passed", "attempts": 3}
{"task": "<task-id>", "unit": "reconstruction/<area>/<Class>.cpp", "attempts": 3, "blocker": null}
```
