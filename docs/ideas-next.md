# Ideas after the third batch: near-misses, large functions, sequencing

Build `sse-steam-1-7-104` (image SHA-256 `846efccf…f1402f`, re-hashed for this work). Continues
`docs/resource-guidelines.md` ("the guidelines") where it stopped: the 9 near-misses of the
40-function batch and the functions over 512 bytes. Task `p6-ideas`, claude-fable-5-2, one host, not
reviewed. Written for the Engineers who will build these; nothing here is implemented.

**Evidence labels.** *Measured* = counted here with original stdlib scripts, private under
`.local/experiments/ideas-next/` (`pass2.py`, `an_pass2.py`: local disassembly plus the image's
`.pdata`, unwind, EH and RTTI data, 21 s; `nm_inv.py`, `nm_inv2.py`: the private side-by-side
listings of the near-miss attempts). *Estimated* = stated heuristic. *Hypothesis* = untested; no
compiler was run for this document. Yields are potentials, never counts of matches.

## 1. What was measured

Population: 106,486 non-funclet, non-thunk entries, 21.87 MB. Share of functions per size class:

| property | <=64 B | 65-128 | 129-256 | 257-512 | 513-1024 | >1024 | functions |
|---|---|---|---|---|---|---|---|
| 2 or more callee-saved registers in the unwind codes | 8% | 52% | 84% | 94% | 96% | 97% | 54,490 |
| 4 or more | 0% | 3% | 35% | 72% | 88% | 94% | 24,426 |
| language handler (C++ `FuncInfo` readable: 39,397) | 9% | 55% | 44% | 54% | 58% | 61% | 39,848 |
| at least one `lock`-prefixed instruction | 2% | 7% | 15% | 26% | 31% | 33% | 11,546 |
| inlined spin wait (calls `Sleep`, has a compare-exchange) | 0% | 0.1% | 0.4% | 1.8% | 2.5% | 1.3% | 505 |
| register-indirect jump (jump table, estimate) | 0.5% | 0.3% | 0.5% | 1.0% | 3.9% | 8.6% | 969 |
| try blocks | 0% | 0.1% | 0.7% | 1.3% | 0.4% | 0.1% | 345 |

- **The frame-initialising store of -2** (the EH state slot) is among the first 14 instructions
  of 34,027 functions. All but **19** have a language handler; `0x237a20` is one of the 19.
- **Near-miss listings** (best attempt of each of the 9; 536 target instructions): 61% of rows
  are starred; the instruction edit distance with registers abstracted to width and branch
  targets resolved to instruction indices is 129 (24%), per function 0, 2, 4, 6, 9, 11, 16, 17,
  64. First-mismatch offset is +0 for `0xce3250` when only a register exchange separates it from
  the target, so that offset is not a usable search score.
- **Large functions** (>512 B): 9,226 entries, 10.18 MB. Distinct direct callees: median 7, p90
  18, max 182. Of 85,039 caller-to-distinct-callee edges, 49% go to callees of 128 B or less and
  87% to 512 B or less; 4,060 large functions (44%) call nothing bigger. The 1,000 callees with
  the most large callers (median 109 B) take 54% of the edges and bring 2,293 large functions to
  80% callee coverage; 3,000 bring 3,693. C++ EH: 5,189 (5.74 MB), median 5 unwind states, p90
  14, 38,273 states in all; 27 with try blocks; 487 with a register-indirect jump; 905 L1
  duplicates. By nearest vftable-labelled neighbour (estimate): engine 7,871 (8.48 MB), Havok
  1,034 (1.35 MB), Scaleform 321 (0.35 MB).
- **Recurring code inside functions** (one representative per L1 code: 52,758 functions, 4.14 M
  windows of 8 instructions, registers abstracted to width, call and data targets kept, prologue
  and epilogue excluded): 3,257 distinct windows occur in 20 or more functions. 66% of functions
  of 513-1024 B and 73% of larger ones contain one; 14% and 9% of their instructions lie inside
  one. At most 869 distinct run starts recur in 20 or more functions (82 in 100 or more): an
  upper bound on shared bodies. 1,146 of the windows also occur in a function of 40 instructions
  or less; 4,853 of 8,526 scanned large functions contain one of those.

## 2. The nine near-misses

Classification is my estimate from mnemonic-level differences in the private listings.

| RVA | residual difference in the best attempt | probable cause | answer |
|---|---|---|---|
| `0xce3250` | two callee-saved registers exchanged, nothing else (5 attempts) | allocation order | P3, P4; P8 applies |
| `0xce32d0` | two adjacent instructions in the other order, plus registers | initialisation order of a local | P3, P4 |
| `0x1cdc60` | temporaries in other registers; one sum computed earlier | temporaries, expression order | P3, P4 |
| `0x237300` | sign- versus zero-extension of a switch operand; one compare form | signedness or width of a temporary | P3, P4 |
| `0x1cd860`, `0x1ce7e0` | the same two-way "is open" test laid out differently in both; a discarded pointer walk in the second | an inline accessor of the class, used by both | P2 |
| `0x2e73a0` | a test and branch the candidate lacks | an inline cast helper that re-tests its argument | P2 |
| `0x2e5a60` | two register copies before a call the candidate lacks | the callee takes more arguments than declared | P5 |
| `0x237a20` | EH-style frame (state slot, eager saves, larger frame), no handler data | a destructible local or `new` whose protected range became empty | P6 |

Four look reachable by mechanical source variation, four need knowledge that is not in the
function, one is an EH frame. The first class grows with size (first table row), the second
with the share of inlined code.

## 3. Proposals, ranked by expected yield per unit of effort

### P1. Aligned diagnostics and one distance (first; P3 and P7 depend on it)

- **Mechanism.** Align target and candidate by longest common subsequence over instructions
  whose branch targets are rewritten to instruction indices; star only unaligned rows; report
  `d_shape` (registers abstracted) and `d_exact`. `unwind-info-mismatch` names the differing field
  (register set, save order, prologue or frame size). Evidence: 61% starred against 24%
  differing; three handoffs complain about reason codes or stars.
- **Spec.** `tools/verifier/disasm.py`: resolve branch targets to indices and calls or
  RIP-relative operands to bound symbols, align, write distances and hunks to the private
  `diagnostics.json` and one sanitized line `distance shape=N exact=M of T`. Reference:
  `nm_inv.py`. **Test:** the stored attempts of the nine reproduce the distances above; a pass
  gives 0; a synthetic pair differing in one branch target gives 1. **Yield (estimate):** one or
  two attempts per failing function.

### P2. Census of recurring inlined bodies; one verified header per body

- **Mechanism.** The same instruction run inside many functions is an inline helper from a shared
  header. Find the runs, reconstruct each helper once, prove it through the smallest function
  containing it, name it in the brief of every function with the run. The guidelines dropped
  this for lack of a cheap detector; the pass of section 1 is one (11 s).
- **Evidence.** At most 869 bodies; two thirds of large functions contain one; 1,146 windows
  have a small out-of-line twin (a compiled reference, often with a community name); 505
  functions hold an inlined spin wait; 4 of the 9 near-misses.
- **Spec.** `tools/inline_census.py`, output private in `.local/census/`: windows as in
  `pass2.py`; merge overlapping frequent windows into maximal runs; cluster by window set; per
  cluster keep members, offsets, callees and data targets inside the run, twins (the run covers
  half of a function of 40 instructions or less). The exporter lists "recurring bodies: cluster,
  offsets, twin, promoted header" in each pack. An Engineer writes the 20 largest clusters as
  inline members and promotes the headers (guidelines, technique 5).
- **Test.** `0x1cd860` and `0x1ce7e0` share a cluster at their open test; with that accessor
  inline both pass or fall below `d_shape` 3. **Next targets:** the base-object cast of
  `0x2e73a0`, the spin wait, reference-count release bodies (11,546 functions with `lock`).
- **Yield and risk (estimate).** Half of the near-misses and 9 to 14% of the instructions of
  large functions. Frequent windows include argument-setup idioms; the twin test and a callee or
  data target inside the run separate helpers from idioms.

### P3. Source permuter for the pinned compiler, no model in the loop

- **Mechanism.** Apply semantics-preserving rewrites to a near-miss unit, compile each variant on
  the Boat machine, score with P1, keep the best, repeat. A variant at distance 0 goes through
  the normal `attempt`, lint and Reviewer; the comparator stays the only judge.
- **Stage 0 (days).** A private copy of the unit carries choice points `/*PERM{a|b|c}*/` written
  by the failing Drafter or an Engineer; the tool enumerates or samples the product. No parser.
- **Stage 1, automatic rules** (libclang or tree-sitter, rewriting by source range), ordered by
  the nine cases: (R1) order and placement of local declarations; (R2) initialise versus declare
  then assign; (R3) name a subexpression or inline a single-use temporary; reuse a loaded member
  or re-read it; (R4) signedness and width of locals, parameters, return types; (R5) `if`/`else`,
  early return, conditional expression, `&&` versus nested `if`, inverted condition; (R6) loop
  forms; (R7) operand order of commutative operators and comparisons; (R8) move an expression
  into an inline member or inline one by hand; (R9) parameter by value, const reference or
  pointer for callees the unit declares; (R10) `volatile`/`const` on members; (R11) `switch`
  versus `if` chain; (R12) return type and arity of unverified callees. No rule adds dead code or
  anything the lint refuses.
- **Scoring.** `10*d_shape + 3*(d_exact - d_shape) + |size difference|/4 + 5*[unwind differs]`;
  0 only on a comparator pass. Random restarts and keep-best, as decomp-permuter does.
- **Throughput (estimate; measure first).** `attempt` takes 4.7 s median (measured, 86
  attempts), mostly sync, bind and several comparisons; compile plus one comparison should take
  1 to 2 s per core, so 15,000 to 30,000 variants per hour on 8 cores. Budget: 10 Boat minutes
  per function, three times the 194 s an accepted function costs now.
- **Test.** Recovery: 3 random rule steps on each of 10 accepted units; the permuter returns 8
  of them to a pass within budget. Then `0xce3250`, `0xce32d0`, `0x1cdc60`, `0x237300`.
- **Yield and risk (estimate).** 30 to 50% of the allocation class, none of the helper or
  signature class. It is a byte-driven search, which the guidelines declined for layout variants;
  here every rule yields ordinary C++, the result passes the same lint and Reviewer, and a win
  with no cookbook rule to explain it is flagged. Decision 2.

### P4. Matching cookbook

- **Mechanism.** `docs/matching-cookbook.md`: per solved near-miss, the symptom in the
  diagnostics, the source change, and the accepted unit or synthetic pair that proves it. The
  permuter tries the rewrites tagged with a matching symptom first.
- **Evidence.** Rules already paid for and unwritten (handoffs): an out-parameter left
  uninitialised; a by-reference parameter copied to a local; `volatile` on one member only; a
  flag read before a store; one returned object for the return-value optimisation.
- **Hypotheses to test with 20-line synthetic pairs on Boat** (publish the rule only):
  callee-saved registers follow the order in which long-lived values are first defined, weighted
  by loop depth; a late-saved register belongs to a value defined after an early exit; an inline
  helper returning from two branches lays out differently from a conditional expression; a
  narrower signed local changes the extension a `switch` uses.
- **Test.** Unit attempts per pass (78 for 31 in the third batch) fall in the next batch.

### P5. Call-site census for callee signatures

- **Mechanism.** Per callee, over all direct call sites: which argument registers are written
  before the call, whether and at what width the result is read. The pack's reference table
  gains "arity observed at N sites". Evidence: `0x2e5a60`; three handoffs report guessing
  parameters; 2,880 entries have 10 or more callers (guidelines).
- **Test.** For callees of the 31 accepted third-batch functions the census agrees with the
  accepted declarations in 95% of cases; for `0x22b2c0` it reports more arguments than the failed
  draft declared. Hours of work.

### P6. EH skeleton in the pack

- **Mechanism.** Contract v2 decodes the unwind map, try blocks and IP-to-state table; the
  exporter uses them only to bind funclets. Add an "Object lifetimes" table to the pack: state,
  parent state, the destructor its funclet calls (which names the type), first and last offset,
  try and catch ranges. Evidence: 39,397 C++ EH functions; 38,273 states in large ones alone.
- **Test.** For accepted EH functions the table's object count equals the destructible locals
  and temporaries of the accepted source.
- **`0x237a20`.** Hypothesis: a destructible local, temporary or `new` lays the frame out for
  EH, and nothing in its protected range can throw after inlining, so the handler data is
  dropped. Confirm on Boat with a local whose inline destructor is non-trivial and whose scope
  holds (a) only inlined code, (b) one external call: expect the state slot and eager saves in
  both, a handler only in (b). 19 functions: one cookbook entry, no tooling.

### P7. Large functions: order, pre-verified context, partial credit

- **Mechanism.** (1) Schedule a large function when 80% of its distinct callees are accepted or
  stamped. (2) Brief = shared headers of every class it touches (sizes by C4), P2 bodies with
  offsets, P5 signatures, P6 lifetimes, jump-table targets as block offsets. (3) P1's alignment
  per region between consecutive calls, so progress is visible before the function matches;
  private, never a status. (4) Larger attempt budget; permuter last.
- **Evidence.** 1,000 small callees unlock 2,293 large functions, 3,000 unlock 3,693; jump
  tables concern 5% and try blocks 0.3%, so neither needs its own tool.
- **Test.** Pilot of 10 engine functions of 513 to 800 B with 5 or fewer accepted callees and no
  EH, then 10 with EH, under their own cost profile; continue only if tokens per accepted byte
  stay within twice the small-function figure.
- **Yield and risk.** Unknown until the pilot: 46.5% of the bytes, and nothing measured here
  shows it is tractable. Exclude the estimated 1,355 Havok and Scaleform large functions.

### P8. An `equivalent` tier under one strict invariance (fallback; build last, if at all)

- **Defensible: I1, same-length callee-saved bijection.** One bijection on RBX, RBP, RSI, RDI
  and R12 to R15, identity on every other register, applied to the whole function, after which
  the candidate is byte-identical to the target (instruction boundaries, lengths, opcodes,
  prefixes, immediates, displacements, reference targets, block order) and the unwind codes are
  equal after the same rewrite. These registers mean nothing to callers and callees beyond being
  preserved, and both versions preserve what they use.

| candidate definition | qualifies (listing level) | verdict |
|---|---|---|
| I1 | 1 of 9: `0xce3250`, two registers | the only one to adopt |
| I2: I1 with encodings of other lengths | the same 1 | no: lengths move branch forms and alignment padding, so the rest is no longer checkable as identical |
| renaming caller-saved registers | 0 | no: they carry arguments, results and implicit operands |
| adjacent independent instructions reordered | 1 more: `0xce32d0` | no: needs dependence and flag analysis, and is a source difference |
| commutative operand order, equivalent encodings | 0 | no: the compiler is deterministic, so it is a different expression |
| branch layout or block order | 0 | no: graph isomorphism; the TESFile cases also differ in instructions |

- **Sound check.** A transformer in front of the unchanged comparator: decode the candidate with
  a real x86-64 decoder pinned by hash (a byte-level ModRM patcher misses opcode-embedded
  registers, SIB, REX and 8-bit forms), derive the map against the target, rewrite the register
  fields, run contract v2 on the result. Fail closed when a byte does not decode or a second
  decoder disagrees on boundaries; an instruction is off an allowlist of plain forms (no string
  instructions, `cpuid`, `xlat`, 16-byte compare-exchange, legacy high-byte registers, RBP as
  frame register); the map is not a bijection or touches RSP or a caller-saved register; the
  function has a language handler or chained unwind entries (version 1).
- **Negative tests, each must fail:** two registers mapped to one; one instruction left
  unrenamed; an argument-register exchange; an exchange across a string instruction; unwind codes
  unpermuted or permuted differently; an immediate or displacement changed alongside a valid
  exchange; an exchange that changes an encoding length; a renamed function with a handler.
- **Bookkeeping.** Status `equivalent` with `invariance: {name: "callee-saved-bijection",
  version: 1, map}` in the record; own count and bytes in `data/progress.json`, on the site and
  as a cost profile; never summed with matched; replaced by `matched` when a later source
  passes, old record kept. Reviewer: usual plausibility; record names invariance and checker
  version; eligibility documented; no text calls it a byte match.
- **Against stopping early.** Granted by the validator only and absent from the Drafter card;
  requires an exhausted attempt budget, a spent permuter budget whose best is `d_shape` 0, and an
  Engineer triage note. Re-queued whenever a cookbook rule on callee-saved order is added. Above
  5% of matched, dispatch pauses for review.
- **Recommendation.** Yield is 1 of 9 near-misses (1 of 40 drafted). Build it only if P3 and P4
  fail on the lock functions; one rule for register order makes it unnecessary.

### Considered and not proposed

Tooling for the 19 handler-less EH frames, for jump tables (969, estimate) or for try blocks
(345): too few functions. A model inside the permuter loop: the Drafter already is that loop.
Compiling pieces of a large function separately: allocation and layout are whole-function
decisions, and the region score gives the visibility without a false claim. Per-function recipe
search: no near-miss of this batch points at flags.

## 4. Sequencing, and a plan for the next 1,000 accepted functions

1. **P1** (verifier diagnostics; no contract change).
2. **P4** from existing handoffs, **P5**, **P6** (exporter only); in parallel the guidelines'
   class skeletons and fan-in planner.
3. **P2** and the first 20 shared headers (validator: a header change re-verifies its units).
4. **Solve one, stamp the cluster** (guidelines, technique 2; validator: batch Reviewer sampling,
   cost profile for stamped members).
5. **P3** stage 0, then stage 1 (worker: a compile-and-compare entry point outside
   `max_attempts`, with a per-function Boat budget).
6. **P7** pilot once 1,000 small callees are accepted or stamped.
7. Initializer generator (guidelines, technique 3; contract v3) and **P8**, each on a yes only.

All figures are estimates in ledger units (cache reads counted per message):

| part | functions | model tokens | Boat |
|---|---|---|---|
| stamped from about 50 solved patterns | 550 | 50 pattern solves; batch reviews about 15M cache-read | 550 x 20 s: 3 h |
| drafted in class units, 80% pass rate | 450 of 560 | 280M cache-read (0.5M each), 8M output; Reviewer 36M | 6 to 24 h of confirms |
| permuter on about 110 near-misses | recovers 30 to 50 | none | 110 x 10 min: 18 h |
| Engineer tooling, steps 1 to 5 | n/a | 60M to 120M cache-read | 1 to 2 h |

Total: 0.4 to 0.6 billion cache-read tokens, 12M to 20M output tokens, 30 to 50 Boat hours,
uncertain by a factor of two either way: the drafted figure rests on five second-batch functions
(0.57M Drafter cache-read each) and one 40-function batch; stamping and the permuter have never
run. These 1,000 are small functions, under 1% of the bytes; byte progress starts with step 6.

## 5. Decisions for the maintainer

1. **`equivalent` tier (P8).** Adopt I1 only, built after the permuter, or decline the tier.
2. **Permuter-found sources (P3).** Is a variant found by mechanical search acceptable when it
   passes the same lint and Reviewer and its change is a recorded cookbook rule? The card forbids
   "odd control flow only to force bytes"; no rule produces that, but the search is byte-driven.
3. **Permuter Boat budget:** 10 minutes per function, proposed cap 20 hours per 1,000 functions.
4. **Shared headers (P2).** Does a unit keep its accepted status without a new Reviewer pass
   when only a shared header changed and the unit re-verified?
5. **Large-function pilot (P7).** 20 functions, own cost profile, the stop rule above.
