# Drafter card: normal functions

One class per unit; usually 6–10 functions, mostly 65–512 bytes. Use this card with
`docs/drafter-runbook.md`, passing the queue directory from the brief to every queue command.
Read `sheet.md` and one function's numbered pages at a time. Luna reads only plain `.md`
sheets, never `.fnv.md`. All five binding rules of the runbook apply.

## Loop

1. Skeletons are already installed. Open the two files named by the sheet; replace body markers
   with your own C++, model/origin placeholders with truthful values, and unresolved type notes
   with declarations. Do not change a shared header or a different unit.
2. Start with the shortest function. Read all its pages before coding: signature, memory operands,
   calls, target listing, then the decompiler hint. Never paste listing or decompiler text into source.
3. Declare members at observed offsets, keeping padding and every size assertion correct. Declare
   called functions without bodies so attempt can bind them; add missing addresses from the sheet
   only to this task's `bind-hints.json`.
4. Run `tools/verifier/attempt <unit dir>` in the foreground. Read the first compile error or each
   function's first mismatch. Change one concrete cause, then attempt again. Do not optimize from
   intuition when the target does different work.
5. A normal unit gets three counted attempts per selected function plus four for shared setup.
   The sheet gives the exact total. The first three compile failures are free, as in the small kit.
   Stop changing a function after three counted attempts with the same first mismatch, or when the
   unit budget is spent. Save it under `<unit dir>/near-miss/<rva>.cpp`, explaining the difference.
6. Run attempt again after setting aside a function so the remaining functions still compile.
   Run `tools/lint_reconstruction.py <h> <cpp>` and `tools/check_labels.py <h> <cpp>`; fix every
   finding, attempt again after a code change, then report with `work_queue.py done` and take the
   next unit. The runbook gives the exact result format.

## Locals, branches, loops and calls

- **Types first.** Match the width and signedness of loads, stores, arithmetic and comparisons.
  A byte flag is not a 32-bit integer. A sign-extending load and unsigned comparison need distinct
  attention. Keep pointer arithmetic in the same element width as the target.
- **Locals.** Name every added local with a `GUESS(low)` label. Introduce a local only for a value
  the target keeps across work. A repeated memory read may be intentional; do not automatically
  cache it. Stack slots may be reused, so a decompiler's many temporaries need not be many locals.
- **Branches.** Recover null checks, early returns and side-effect order before shortening the code.
  Short-circuit conditions can skip calls; preserve that behavior. Check the listing's branch
  directions rather than trusting the decompiler's chosen condition spelling.
- **Loops.** Identify initialization, the back edge, the termination test and the increment. Preserve
  pre-test versus post-test form, iteration width, stride and stores. Do not replace a loop with
  a standard algorithm unless the target supports that shape.
- **Calls.** The sheet's call target and register arguments are evidence; an inferred callee name is
  a guess. Declare its return and argument types carefully. A call may write through an output
  pointer. Do not turn it into a return value without evidence.
- **Tail calls.** A final jump to a callee needs the call as the final statement, usually
  `return Callee(...);`. Keep no local object alive after it. A `CALL` followed by `RET` is different.
- **Object lifetime.** Constructors and destructors affect vftable stores, cleanup and unwind data.
  Keep the skeleton's constructor when a deleting destructor needs it emitted. If the target
  calls an out-of-line destructor, declare it without defining it. Use the small card's destructor
  rules when needed; never change an accepted shared base header to force a result.
- **Frame/unwind mismatch.** Check local lifetimes and called function signatures. Try one concrete
  correction, then preserve the near-miss. Never use assembly, raw bytes, codegen pragmas or remove
  an assertion to silence a layout error.

## Results and labels

`PASS all-checks-passed` is a local pass only. `function-size-mismatch` means the compiled size
is different; `code-byte-mismatch` points to the first differing offset. Read the private
`attempts/<NNN>/0x<rva>/side-by-side.txt`. A compile, lint or binding error is work to fix, not a
reason to stop the queue. Three infrastructure failures in a row stop the session as in the runbook.

Every added name needs an origin label. Copy the skeleton's labels; use a separate line such as
`// index, count: GUESS(low)` for invented names. A size assertion needs its message:
`static_assert(sizeof(X) == 0x20, "X size");`. Use quoted relative includes as the skeleton gives them.
Never edit task.json, symbols.json, tools, docs, another unit, or the queue files directly.
Never commit, push, mark matched, start agents, or access a remote machine.
