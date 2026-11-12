# Small-function Drafter card (version `small-1`)

For small functions (accessors, initialisers, flag tests, forwarders, empty or deleting destructors).
This card is all you need; `docs/drafter-card.md` and `docs/matching-cookbook.md` are optional, for hard cases.

Words: a **unit** is one class, `reconstruction/<area>/<Class>.h` + `.cpp`; its **unit dir** is `.local/tasks/<group>/<dir>`.
**RVA** is a function's address in the game (`0x4aa860`). **attempt** compiles the unit remotely and
compares its bytes with the game. Everything under `.local/` is private: never paste it anywhere.

## The loop, per unit (in the order the task gives)

1. `python3 tools/skeleton.py <unit dir>` writes both files. "already exist" means: edit them.
2. `python3 tools/sheet.py <unit dir> --function <rva>` for each function (`--page 2` if it says so).
3. Edit the files. Replace every `SKELETON_TODO_BODY;` with the body. In the `.cpp` header, replace
   `SKELETON_TODO_MODEL` with your model name. Turn padding into the members the bodies read.
4. `tools/verifier/attempt <unit dir>`. One unit per command; never in the background.
5. Read the result line of each function and act on the table below. Repeat 3 to 5.
6. When every function passes, or the unit is stuck: replace `SKELETON_TODO_ORIGIN` with `none`
   (or, if attempt printed `origin advice:`, name the body you adapted, its file and licence). Run
   `python3 tools/lint_reconstruction.py <h> <cpp>` and `python3 tools/check_labels.py <h> <cpp>`, fix
   every finding, and run `attempt` again if you changed code.
7. Append the unit's result lines to the handoff (end of card). Go to the next unit.

## Rules for small functions

1. **Members.** Sheet "Memory operands" `0x18 RCX byte` is a 1-byte member of `this` at 0x18. Split the
   padding, keep the size check: `std::uint8_t unknown18[0x8];` -> `bool data; std::uint8_t unknown19[0x7];`.
2. **Accessors and forwarders** are one line: `return data;`, `return 3;`, `return a_other->Get();`.
3. **Store order follows the target.** Write assignments in the order the listing stores them.
4. **Deleting destructor** (sheet "Kind: scalar deleting destructor"): keep the skeleton's constructor (it
   makes the compiler emit the compared body). Listing stores the vftable, then calls: `X::~X() {}`. Listing
   only calls one function, then tests `EDX` bit 0: delete the definition, keep `virtual ~X();`.
5. **Declare, don't define, a function the target calls:** `void Reset();`, no body; attempt binds it.
6. **Flag test** (`shr eax,3; test al,1`): `inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
   { return ((a_flags >> a_bit) & 1) != 0; }`, call `TestBit(flags, 3)`, label `// TestBit: GUESS(low)`.
7. **Null test the target repeats:** read the member again instead of keeping a local copy.
8. **`static_assert` needs a message:** `static_assert(sizeof(X) == 0x20, "X size");`.
9. **Includes:** own header `#include "X.h"`; others only as the skeleton gives them (`"../area/Y.h"`).
10. **Labels.** A label line is `// <names>: <LABEL>`; LABEL is `COMMUNITY(<owner>/<repo>@<rev>, <licence>)`,
    `GUESS(low)`, `EXE_RTTI`, `OBSERVED`, or `STANDIN` plus one of those. Copy the skeleton's labels;
    add one for every name you add. Never write the label words anywhere else.

Never write `asm`, `##`, `#pragma` (except `once`), byte arrays, `\x` strings. Never edit `task.json`,
`symbols.json`, tools/ or another unit.

## Result lines and what to do

| attempt says | means | do |
|---|---|---|
| `does not exist yet` | no .cpp | run step 1 |
| `COMPILE FAILED` + error lines | C++ error (`SKELETON_TODO_BODY`: a stub left) | fix that line, attempt again (first 3 free) |
| `UNBOUND reference <name>` | a callee without an address | add `{"<name>": "0x<rva from the sheet>"}` to `<unit dir>/bind-hints.json` |
| `UNBOUND function` | your function was not found | check its class and name match the sheet |
| `PASS all-checks-passed` | bytes match | done with that function |
| `function-size-mismatch size A/B` | yours is A bytes, target B | compare listings; add or remove the missing work |
| `code-byte-mismatch at +0xNN` | first different byte | read `attempts/<NNN>/0x<rva>/side-by-side.txt` at that offset |
| `unwind-info-mismatch`, `eh-...` | frame or exception layout | try one change; then save as near-miss |
| `budget exhausted` | no attempts left | save near-misses, write lines, next unit |

**Stuck** = three counted attempts with no change in the first mismatch, or the budget is spent.
Then move the function and the header lines only it needs to `<unit dir>/near-miss/<rva>.cpp`, first
two lines: `// <reason>, size A/B, attempt N` and one sentence on the remaining difference. Run
`attempt` once more so the rest passes.

## Never stop early

- A lint, label, compile or tool error is never a reason to stop: do what the message says, continue.
- A stuck unit is skipped, not the group. Stop only when every unit is done or every budget is spent.
- Never commit, push, mark anything matched, or stop a machine.

## Handoff (always write it, even if nothing passed)

Append JSON lines to `.local/handoffs/<group>.jsonl`, one per function, then one per unit:

```json
{"rva": "0x4aa860", "result": "pass", "reason": "all-checks-passed", "attempts": 2}
{"task": "<unit task id>", "unit": "reconstruction/bsengine/X.cpp", "attempts": 2, "blocker": null}
```
`result` is `pass` or `fail`; `blocker` names the near-miss file or the problem, else `null`.
