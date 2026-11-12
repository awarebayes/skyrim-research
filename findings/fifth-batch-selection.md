# Finding: fifth batch of 223 functions in 99 classes, chosen for a low cost per function

Status: OBSERVED properties of the pinned image; selection only. Nothing reconstructed or compared.
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), task p16-batch5-prep; local only
Date (UTC): 2026-11-12
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): private plan `.local/packs/_plan/fifth-batch/` (list, plan, inventory rows)
Source exposure: mixed (binary-analysis of the pinned image: its .pdata, EH, RTTI and code bytes through the private function table; community-headers; community name databases; the FNV sibling index)
Sources and immutable revisions / licenses: CharmedBaryon/CommonLibSSE-NG `b93280e832f263dbef44e44cbe2936622a02f91a` (MIT); powerof3/CommonLibSSE `654e55f7979c1733033d5dbef176e43827bac944` (GPL-3.0; files carrying its declarations state GPL-3.0); Address Library 1.7.104.0; meh321's name list `skyrimae.rename`, used with the author's permission as reported by the maintainer (`docs/authorizations.md`); momusdigital/fnv_decomp `91e1b6e8` (no licence; used by maintainer decision, pointers only)
Name provenance: COMMUNITY (unverified), class names EXE_RTTI
Confidence: high for counts and the filters; medium for class attribution; low to medium for names; the expected pass rate is a guess from the fourth batch

## Question and method

Which functions should the next Drafter wave take so that one Drafter covers many functions at a
low cost each? A Drafter run has a fixed start-up cost and a per-function cost; in the fourth batch
small functions passed in one or two attempts. `export_pack.py plan --order cheap`
(`tools/ghidra/plan_cheap.py`) starts from the whole-image table of `build_function_table.py` and
keeps ordinary, v2-ready, community-named functions of classes that pass the per-class checks
(`findings/fourth-batch-selection.md`), and then also requires:

- at most 500 bytes, no exception-handling data (no language handler at all);
- no thread-local read: the function's bytes are scanned for the `gs:[0x58]` load that starts
  every `__declspec(thread)` access in this image;
- not in the two parked families of the census in `findings/whole-program-optimization.md`
  (callee-saved saves that skip the first home slot; an EH state store without a handler);
- a class whose skeleton is verified (a community header passes C1 to C3 and the size is read from
  the deleting destructor, C4);
- no class that already has a unit in `reconstruction/` or an open task: extending an accepted
  unit re-opens its records, and two tasks on one unit would collide.

Ranking: an FNV counterpart (a same-named method, or an agreeing slot, in the sibling index; one
more point for an optimised `/O2` counterpart), a class with entries in the FNV inline-helper
catalogue, size (at most 64 bytes first, then at most 128), a base class whose header already exists
in `reconstruction/`, then fan-in. One function per L1 cluster: the other members are the stamping
lane's. Then grouping: classes with at least six selected functions, most of them over 64 bytes,
become **normal** tasks (one class, 6 to 10 functions); the small functions of the remaining
classes form **small** tasks of 15 to 25 functions, one unit per class, grouped under the nearest
common RTTI base that gathers at least 15 of them. 60 functions were reserved for normal tasks.

## Observations

- Eligible after all filters: 1,579 functions; 982 after one per L1 cluster. Removed by the new
  filters (after the existing ones): exception data 539, existing unit or open task 706, no verified
  skeleton 213, parked family 34, thread-local read 12 (183 of the 3,083 scanned functions read
  thread-local data; most were already out for other reasons), families too small for a task 91.
- Selected: **223 functions, 11,290 bytes, 99 classes**, in 15 tasks: 8 small (168 functions, 92
  units) and 7 normal (55 functions), plus the ten undrafted fourth-batch tasks (68 functions, 6,543
  bytes) for a wave of 291 functions.
- Size bands: at most 32 bytes 98; 33 to 64 86; 65 to 128 22; 129 to 256 15; 257 to 512 2.
- Areas (prefix rule): forms 136, netimmerse 59, bsengine 28.
- FNV: 49 functions have a counterpart in the sibling index (26 of them `/O2`); 140 sit in a class
  with inline-helper catalogue entries; 152 have one or the other.
- Clusters: 73 of the 223 are members of an L1 cluster with more than one member (each the only one
  of its cluster in the batch).
- Name sources of the first usable name: NG slot 166, po3 slot 35, meh321 16, po3 id 4, NG id 2.
- One normal task (`NiPointLight`) holds two functions that test float equality without a parity
  branch; its other functions are recipe-neutral, so the task uses the `o2-fpfast` recipe.

| task kind | tasks | units | functions | bytes | budget (counted attempts) |
|---|---|---|---|---|---|
| small | 8 | 92 | 168 | 5,087 | 383 |
| normal | 7 | 7 | 55 | 6,203 | 193 |

## Interpretation and alternatives

Most of the batch is accessors, data initialisers and deleting destructors of form components and
scene-graph classes, the shapes that passed fastest before. Classes with an accepted unit were left
out rather than extended, so no record goes stale; their headers are offered to new units instead
(the task brief lists them). An alternative would take more functions from the accepted classes and
re-confirm them with the unit; that costs a Reviewer pass per extended unit while the label-only path
is held to label and comment diffs.

## Reproduction and sanitized evidence

`python3 tools/ghidra/export_pack.py plan --order cheap --label fifth-batch --total 232 --task-prefix
batch5- --parked <census.json> --catalogue <inline-candidates.json> --evidence
findings/fifth-batch-selection.md`, then `export_pack.py packs <list> --class-material
--shared-classes-name _shared-classes.batch5.json --fpfast unit`. Inputs and outputs are private.

## Negative results and limitations

The pass-rate expectation is extrapolated from the fourth batch, not measured. The thread-local scan
sees only the `gs:[0x58]` load in the function's own bytes, not a thread-local access in an inlined
callee's out-of-line part. The parked-family census is per function and dated to the comparator of
that census. Shared-header suggestions are by name; most accepted headers are minimal and may lack
the virtual slots a derived class needs. Rows are added to `data/progress.json` as `mapped`.

## Reviewer and outcome

Not reviewed.
