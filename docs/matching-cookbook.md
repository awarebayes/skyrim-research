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

**14. A vtable slot 0 destructor is the deleting destructor, `??_G` (or `??_E`), not `??1`.**
(high)
Symptom: `function-size-mismatch` on `X::~X`, the target larger than the candidate, its listing
testing bit 0 of the second argument and calling operator delete under it. The compiler always
emits the plain `??1` separately; the slot body is `??_G` with the destructor inlined, emitted
only beside the vftable, so the unit must define a constructor (or otherwise reference the
vftable). `attempt` reads the kind from the pack (`task.json` `functions[].destructor`) and binds
it; a bind hint it cannot use is printed as a WARNING. Closed TESGrass 0x270890.

**15. An inlined map lookup matches through a bool helper that writes its out-parameter only on
a hit.** (medium)
Symptom: the target's inlined lookup leaves the caller's local untouched on a miss, where a
candidate returning the value (or a default) stores on both paths. Fix: write the lookup as
`bool Find(key, T& out)` that assigns `out` only when found and returns whether it did.

**16. A flag bit tested as load, `shr`, `test al,1`: a by-value bit-index helper.** (high)
Symptom: the target reads a flag word into a register, shifts it right by the bit number and
tests the low byte (`mov eax,[rcx+0x10]; shr eax,3; test al,1`); the candidate has
`test byte ptr [mem],imm`, `test dword ptr [mem],imm` or `bt`. Cause: MSVC folds every mask, bit-field
or direct `(flags >> n) & 1` spelling of the member into a memory test; the shift survives only
when the word and the bit number reach the test through an inlined call. Fix, first thing to try:

```cpp
// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value.
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}
... if (TestBit(formFlags, 3)) ...
```

For a bit-field struct, pass the whole word (`*reinterpret_cast<const std::uint32_t*>(&flags)` in
a small accessor). A bit-0 test the target does as `movzx eax, byte ptr [mem]; and al,1` is the
same helper on the low byte. The label is `GUESS(low)`: the helper's name and the engine's real
accessor are unknown. Its probable origin is a flag accessor that takes a bit index (the shape
says index and shift, not mask), not the community wrappers: `stl::enumeration::any()` and
`REX::EnumSet::any()` test `(_impl & mask) != 0`, the expression that folds (not tried as a
by-value copy). Closed Character::SetCrimeFaction 0x67eab0, TESObjectCELL::GetLocation 0x2bb180
and NiNode::OnVisible 0xee2cc0; it also fixed the flag tests of NiNode::UpdateDownwardPass
0xee24d0 and TESNPC::ClearData 0x3bbf50, which still differ elsewhere (rules 19, 20).

**17. `static_assert` needs a message.** (high)
The recipe compiles as C++14 (no `/std:c++17`), so `static_assert(sizeof(X) == 0x10);` is a
compile error. Write `static_assert(sizeof(X) == 0x10, "size");`.

**18. A deleting destructor that calls the plain one: declare `~X();` and do not define it.**
(medium)
Symptom: the target's `??_G` calls the plain destructor; the candidate's `??_G` inlines a vptr
store and the base destructor calls instead. Cause: defining `~X()` in the unit lets the compiler
inline it into `??_G`. Fix: declare the destructor out of line without a definition and bind
`??1X@@...` to the target's callee with a bind hint; the `??_G` is still emitted beside the vftable
(rule 14). Closed Character's destructor 0x73abc0.

**21. A read through `gs:[0x58]` indexed by `_tls_index` is a `__declspec(thread)` variable.**
(medium)
Symptom: the target loads `_tls_index`, reads the TLS array at `gs:[0x58]`, indexes it and adds a
small constant, the variable's offset in the TLS template; an ordinary global gives a `REL32`
where the target has that constant, and an intrinsic `__readgsqword` read changes the frame and
registers. Fix: declare `extern __declspec(thread) T name;` (a thread-safe function-local static
reads the CRT's `_Init_thread_epoch` the same way) and bind it with the hint
`{"<decorated name>": "tls:0x<offset>"}`; `_tls_index` needs no hint. Give each variable one name
and offset for every function that uses it. Compared from comparator 0.5.0 on (earlier:
`unsupported-relocation` SECREL); measured on synthetic code only. Seen in TESForm 0x1e6930 and
0x1e5b30, not yet closed.

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

**19. A struct copy whose last store moves one slot earlier.** (low)
Symptom: copying a bound (three floats then a float radius), the target loads the radius early
and stores it last; the candidate stores it one store earlier than the source order, whether the
radius is cached in a local or stored before the last centre component. A direct
`radius = other.radius` and a `center = other.center` struct copy change more (an 8-byte `movsd`).
Not closed: NiNode::UpdateDownwardPass 0xee24d0 (code-byte-mismatch, two stores swapped).

**20. A pointer loop that the compiler turns into a counted loop.** (low)
Symptom: the target walks an array with `it != end` (two callee-saved registers, no trip count);
the candidate computes a trip count with `lea`/`shr`/`cmova` and needs two more callee-saved
registers, so the prologue differs. A raw pointer loop and a range-for over `begin()`/`end()` both
give the counted form. Not closed: TESNPC::ClearData 0x3bbf50.

## Method and permuter recommendations

- Compile many variants per attempt: temporary `LabNN` members with candidate bodies in the same
  unit, one `attempt`, then score each variant locally against the normalised pack listing
  (relocations masked, branch targets as `T`). Strip lab code before the final attempt; only a
  real `attempt` pass counts. A permuter should use this as its inner loop (10 to 20 per compile).
- Generate variants as AST rewrites from the rules above, not random token edits: reload or cache
  a member (1), flip a two-way check (2), duplicate or merge a helper call (3, 4), add the live
  argument (5), change the switch width (6), extract a value or a bool decision into a helper
  (7, 8), drop an initialiser (9), add class operator new/delete (10), route a flag test through
  a by-value bit-index helper (16).
- Score the prologue and unwind info apart from the body. A register-only diff with identical
  mnemonics (12) or a -2 UnwindHelp store with no handler (13) should stop the search and go to
  triage: no source permutation tried here changes them.
- Reject variants that add code only to steer register allocation (rule 12's counter tricks),
  even when they score higher.
- Watch inlining: extra lab copies can stop a helper being inlined, so a variant that shrinks
  sharply must be rescored alone (`__forceinline` is acceptable in lab code only).
