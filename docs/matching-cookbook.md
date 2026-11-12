# Matching cookbook

Rules from closing near-misses with `reconstruction/recipes/msvc-19.16.27054-o2.json` on build
`sse-steam-1-7-104`, learned from comparator passes and lab compiles. They describe how this
compiler reacts to source shapes, not what the original said, and are starting hypotheses, never
evidence. Spellings must still meet `docs/drafter-card.md`. Confidence: **high** = closed a
function and the counter-variants failed; **medium** = closed one function; **low** = unsettled.

## Control flow and redundancy

**1. A null test the candidate lacks: re-read the pointer.** (high)
Symptom: the target tests a pointer for null after it was already dereferenced; the candidate
drops the test, so it is shorter with an early mismatch. Cause: the original re-reads the member
or accessor (`GetBaseObject()`, `entry->object`) after a call or in a case body. A value MSVC has
already dereferenced is proven non-null, but a reload counts as a new value. Fix: read the member
again where the target tests it instead of keeping a local. Closed CanBeMoved 0x2e73a0 and the
worn-item test in VisitWornItems 0x237300.

**2. A shared conditional jump merged in the wrong place: reorder a two-way check.** (high)
Symptom: in an "already open?" check over two fields, the candidate merges the two tests' jumps
or puts the arguments of the following call in a different order. Fix: test the non-thread-safe
branch first, with early returns
(`if (!g || !flag) { if (file) return; } else if (handle) return; Open();`), and keep a single
call site. Two call sites, a ternary, or a bool helper that yields `setne` do not match. Closed
TESFile::Seek 0x1cd860 and Duplicate 0x1ce7e0, which share the helper.

**3. A dead loop or a redundant test in a loop: an inlined helper was called twice.** (medium)
Symptom: the target has a loop that is not rotated, a computed value that is never used, and a
null test that repeats. Cause: a null-checking helper is called in both the loop condition and the
body: `while (Root(p->parent)) p = Root(p->parent);`. Fix: write it that way rather than with one
cached call. Closed Duplicate 0x1ce7e0.

**4. A computation hoisted above a check: the source computed it first, or the predicate is a
helper called twice.** (medium)
Symptom: in the target a load or an address computation comes before a flag test, and the same
test appears twice. Fix: put the test in a small predicate (`IsCompressed()`) and call it at both
places. Load the limit and compute the position in source order before the second test. Closed
SeekNextSubrecord 0x1cdc60.

**5. A live argument register at a call means the callee takes that argument.** (high)
Symptom: argument registers are shuffled at one call (for example `this` in r8, an offset in
ecx), and a register the candidate does not set (here edx) still holds an earlier value. Fix:
capture that value before the intervening test and pass it as an extra parameter of the matching
width (here the 1-byte form type). Closed HasQuestObject 0x2e5a60. Check every call whose
argument setup differs for a value the target leaves in rdx, r8 or r9.

**6. Register differences in a switch: change the width of the switch operand.** (medium)
`switch (static_cast<std::uint32_t>(byteField))` and switching on a byte enum give different
register allocation and different zero-extension placement. Try both. Closed VisitWornItems.

**7. A missing shared constant: put the value-producing branch in its own helper.** (medium)
Symptom: the target materialises `-1` once and reuses it for both the compare and the result.
Fix: `int32 mask = -1; if (slot != -1 && slot < 10) mask = table[slot]; return mask;` in a helper.
An explicit `case kLight: mask = 0;` keeps a separate case where the default would otherwise
absorb it. Closed VisitWornItems.

**8. A jump that skips the caller's fallback: an early `return false` inside a bool helper.**
(medium)
Symptom: one target path jumps straight past a fallback test (`|| object->type == kLight`) that
the candidate evaluates. Fix: wrap the whole decision in a bool helper, so the null-object path
returns false before the fallback. Closed VisitWornItems.

## Data and calls

**9. Uninitialised locals are part of the source.** (medium)
Symptom: the candidate has an extra zero store to a stack slot that is later passed by address.
Fix: drop the initialiser (`char* message;`) when a callee fills it and the value is only
released. Closed Seek 0x1cd860.

**10. `delete p` called through the scalar deleting destructor with flag 1: the class has its
own operator new/delete.** (high)
Symptom: the target calls one function with edx = 1 where the candidate calls the destructor and
then `operator delete(p, size)`. Fix: declare class-scope `operator new`/`operator delete` (Bethesda
heap classes have them) and bind the deleting destructor to the target's callee. Inside a `try`
region MSVC splits the call again. Seen in RemoveFavorite 0x237a20.

**11. Missing virtual slots shift every virtual call.** (high)
A call through slot N needs N - 1 earlier virtuals in the stand-in, including the inherited
TESForm slots; add placeholders labelled GUESS. Used for CanBeMoved (slot 0x42).

## Unsolved patterns

**12. A pure callee-saved register swap with the same instructions.** (low)
Symptom: every instruction matches except which callee-saved registers hold `this` and a loop
counter. The comparator reports unwind-info-mismatch at +0x0 with equal sizes. In this recipe,
about 45 source spellings never move `this` out of rbx. Only spellings that add counter
references flip it, and those add instructions. Hypothesis: the original was compiled with /GL
and linked with LTCG (the Rich header lists LTCG C++ objects), or with PGO, which weight blocks
differently. Settle it with a verifier link step (/GL plus /LTCG into a DLL) on unchanged source.
Probably explains BSReadWriteLock::LockForRead 0xce3250 and LockForWrite 0xce32d0.

**13. A -2 store to the UnwindHelp stack slot, eager saves of callee-saved registers, and no EH handler.** (low)
Symptom: the prologue stores the C++ EH UnwindHelp slot and saves rbx/rbp/rsi/rdi before any
early return, yet the unwind info has flags 0. Because shrink wrapping is off, every register
differs from a candidate that does not use EH. In lab compiles, a destructor-bearing local around
a throwing call keeps a handler. Locals whose scope has no throwing call, noexcept or throw()
helpers, and try/catch all either drop the -2 store or keep a handler. Hypothesis: EH state that
the compiler removed only after cross-module inlining (LTCG) or after a late optimisation. Settle
it with the same LTCG experiment plus a variant with a destructor-bearing iterator in the inlined
list helper. Probably explains RemoveFavorite 0x237a20, and any target with the -2 store but no
handler.

## Method and permuter recommendations

The permuter that mechanises rules 1, 2 (inversions only), 6 and 9 is
`tools/verifier/permute.py`; see [permuter.md](permuter.md) for its rules and measured yield.

- Compile many variants per attempt: temporary `LabNN` members with candidate bodies in the same
  unit, one `attempt`, then score each variant locally against the normalised pack listing
  (relocations masked, branch targets as `T`). Strip lab code before the final attempt; only a
  real `attempt` pass counts. A permuter should use this as its inner loop (10 to 20 per compile).
- Generate variants as AST rewrites from the rules above, not random token edits: reload or cache
  a member (1), flip a two-way check (2), duplicate or merge a helper call (3, 4), add the live
  argument (5), change the switch width (6), extract a value or a bool decision into a helper
  (7, 8), drop an initialiser (9), add class operator new/delete (10).
- Score the prologue and unwind info apart from the body. A register-only diff with identical
  mnemonics (12) or a -2 UnwindHelp store with no handler (13) should stop the search and go to
  triage: no source permutation tried here changes them.
- Reject variants that add code only to steer register allocation (rule 12's counter tricks),
  even when they score higher.
- Watch inlining: extra lab copies can stop a helper being inlined, so a variant that shrinks
  sharply must be rescored alone (`__forceinline` is acceptable in lab code only).
