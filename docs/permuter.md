# Source permuter

`tools/verifier/permute.py` searches for a source spelling of one near-miss function that compiles
to the target's bytes, with no model in the loop (proposal P3 in [ideas-next.md](ideas-next.md),
in the spirit of decomp-permuter). It is step 7 of the operating procedure in
[pipeline-review.md](pipeline-review.md): run it on a near-miss before an Engineer triages it.
A permuter result is a draft like any other. It is evidence of nothing until `attempt` passes on
the winning source, the lint passes, and a Reviewer approves it under the rule in
[verification.md](verification.md).

## Use

```sh
tools/verifier/permute.py run .local/tasks/<task-id> --rva 0x<rva> --dry-run   # local: lint and mutation sites, no Boat time
tools/verifier/permute.py run .local/tasks/<task-id> --rva 0x<rva> [--budget 600] [--seed 1]
```

The task directory is the one `attempt` uses (task.json, symbols.json); the function is found in
the compiled file by its community name (`--function Class::Name` overrides it) and must have
exactly one definition there. `--source-root DIR` reads `reconstruction/` from a private copy
instead of the checkout, so a near-miss draft never has to be in the working tree. The run uses
the standing machine like `attempt` (it resumes it unless `--no-resume`), works in
`~/tasks/permute/<task-id>-0x<rva>` (`--remote-root` to change), and removes that directory at the end.

Outputs go to `<task-dir>/permute/0x<rva>/` (private): `best.cpp` (the whole unit with the best
body), `history.jsonl` (every scored candidate: parent, mutations applied, distance and its
components, object hash, compile seconds), `result.json` (start and best distance, candidates,
timings, candidates per Boat minute, comparator result) and `final/` (the comparator's files for
a distance-0 winner). Exit 0 only when the comparator passed. Then copy the body into the unit,
tidy its spelling, and run `attempt`; the Reviewer sees the mutation list from `history.jsonl`.

## What it does

1. **Mutations.** Seeded rewrites of the one body at token and statement level (a statement
   splitter and an operand recogniser, not a C++ parser). A candidate stacks one to three:

   | name | rule | rewrite |
   |---|---|---|
   | `decl-swap`, `decl-move` | R1 | swap adjacent locals; move a call-free declaration to block start or first use |
   | `decl-split` | R2, cookbook 9 | `T x = e;` and `T x; x = e;` |
   | `temp-inline`, `temp-introduce` | R3, cookbook 1 | inline a single-use temporary or re-read a member at each use; name a repeated member read |
   | `if-invert`, `early-return`, `and-split` | R5, cookbook 2 | `if/else` inversion; early return versus nested `else`; `a && b` versus nested `if` |
   | `loop-form` | R6 | `for` versus `while` (no `continue` in the body) |
   | `int-type` | R4, cookbook 6 | signedness and width of an integral local; a cast on the `switch` operand |
   | `compare`, `commute`, `test-form` | R7 | compare direction and operand order; commutative operands; `!x` versus `x == 0`, `nullptr` versus `0` |
   | `increment` | | `++i`, `i++`, `i += 1`, `i = i + 1` |
   | `out-init` | cookbook 9 | a local whose address is passed keeps or drops its zero initialiser |

   Some rewrites can change meaning (a width, a re-read across a call). That does not matter
   for the search, because only identical bytes count, but the Reviewer still reads the result
   against the target. `--also` adds helper bodies of the same file to the search (a helper's
   steps are recorded as `<rule>@<n>`). Cookbook rules 3 to 5, 7, 8, 10 and 11 add helpers, parameters or class
   members; they are outside the one body and are left to the Drafter or Engineer.
2. **Lint gate.** Every candidate passes `tools/lint_reconstruction.py` before it is compiled;
   the unchanged unit must pass too, or the run stops before using the machine.
3. **Batches.** The candidate bodies of a batch go up as one compressed file (`boat scp`), and
   one `boat exec` per batch returns one sanitized JSON line per candidate: distance and components from
   `align.py`, instruction counts, a 16-hex hash of the function's code and relocations, compile
   seconds, error codes on failure. The machine compiles `--jobs` candidates at once (default 4,
   its vCPUs), each worker in its own hard-linked copy of the synced unit, with the recipe's flags
   and the environment `unit_build.py` uses. Compiler output and listings stay on the machine.
   File upload is the transport to use. `--transport inline` exists but is not to be used: it
   puts the compressed candidate source in the exec command line, so reconstructed source would
   sit in the provider's command log (G5 covers placing it on the machine, not in Boat's
   records). Its throughput below is kept as a measurement only.
4. **Search.** Greedy hill-climb on (distance, exact edits, instruction-count difference), with
   sideways moves to new objects of equal score, a random restart from the best after
   `--restart-after` batches without progress, and a seen-set of object hashes, so a spelling
   that compiles to known code does not count as progress. Stops at distance 0, at `--budget`
   seconds of wall time on the machine, or after `--patience` batches without a new best.
5. **Confirmation.** A distance-0 winner is compiled and compared once more by `unit_build.py`
   (pinned toolchain and image checks, include closure, `verify_function.py`). Only that report
   says pass. Distance 0 alone is not a pass: `align.py` is run without the unwind infos.

The run's wall time is queued to the cost ledger as stage `draft`, as `attempt` does. The
budget agreed in pipeline-review.md is 10 Boat minutes per function (`--budget 600`), capped at
20 hours per 1,000 functions.

## Measured (sse-steam-1-7-104, recipe msvc-19.16.27054-o2, standing machine, 4 vCPU)

First trial, nine runs, about 6 machine minutes in total (measured wall time of the runs; the
machine was shared with other agents' compiles):

- **Throughput.** One candidate compiles and scores in a median 0.2 to 0.34 s of a worker's time;
  a batch of 32 on 4 workers takes 1.5 to 2.7 s on the machine. With `--transport inline`, 490
  to 550 candidates per Boat minute (one exec per batch, about 1 s of round trip). With the
  default `scp`, 220 to 340 per Boat minute: the upload adds about 2.5 s per batch. The
  unchanged-unit `unit_build` run at the start costs 2.3 to 5.4 s. The 10-minute budget is
  therefore 2,000 to 5,000 candidates, far more than the rules generate for a small body: most
  runs stopped on patience after 100 to 500 candidates with 4 to 94 distinct objects.
- **Recovery self-test** (accepted functions, three random rule steps, then permuted):
  GetCalcLevel 0x300b90 (2.0 to 0, comparator pass, 17 candidates) and GetDeviceData 0xcfaf60
  (9.5 to 0, pass, 33) recovered; HasOutfitItems 0x2e7fc0 (4.25 to 0.25) and FindPickTarget
  0x5cef10 (0.25 throughout) stopped at one callee-saved register pair, a residue no rule here
  reaches. 2 of 4.
- **Batch-3 near-misses from the Drafter's drafts** (TESFile, before the Engineer's fixes):
  SeekNextSubrecord 0x1cdc60 8.0 to 5.5; Seek 0x1cd860 19.0 to 18.0 with `--also
  TESFile::EnsureOpen` (the step was `out-init`, the cookbook 9 fix the Engineer also made);
  Duplicate 0x1ce7e0 22.75 unchanged. None reached 0: their fixes (cookbook 2 to 4) rewrite a
  helper or call it twice, which the rules do not do.

## Limits

- Bodies only: the target's, plus helpers named with `--also Class::Helper` (same file). No rule
  adds or removes a helper, a parameter, a call or a class member, which is what most of the
  cookbook's closed near-misses needed.
- The definitions must be in the compiled `.cpp`; functions defined in headers are not found.
- No unwind info in the score, so a register-only or frame-only difference (cookbook 12, 13)
  can sit at a small distance forever; stop and triage those instead.
- Text-level rules miss what needs a parser: macro bodies, templates, lambdas, declarations of
  several names in one statement.
