# Drafter card

Everything a Drafter needs. Do not read AGENTS.md or other policy documents; the tools enforce them.
Gates: G1 to G5 granted; private inputs and outputs stay under `.local/` and are never pasted anywhere.

**You get** a context pack (function notes, community types) in your brief and a private task
directory `.local/tasks/<task-id>/` with `task.json` (build id, RVA, size, compiled file, recipe,
attempt budget) and the symbol map. Work in the checkout you are given; do not create worktrees.

**The loop.** Write or edit `reconstruction/<area>/<Class>.h` and `.cpp`, then run
`tools/verifier/attempt .local/tasks/<task-id>` from the repository root (about 5 to 10 s when
warm). It compiles, binds names, compares, and prints one line per function: PASS/FAIL, reason
code, first mismatch offset, candidate/target size. Read locally
`attempts/<NNN>/0x<rva>/side-by-side.txt` (target vs candidate disassembly; `*` marks rows that
differ outside relocated fields) and `compile.log`, revise, repeat. Never stop the machine; it
stops itself at its deadline.

**Names and binding.** Your class and function names may differ from the community names; the
decorated name is read from your object. `attempt` binds functions and references itself and
compares again in the same run; a run that compared nothing because of binding does not count
against the budget. If it prints `UNBOUND ...`, add the name and the RVA from the pack's
reference table to `.local/tasks/<task-id>/bind-hints.json`, for example
`{"BSTimer::QGlobalTimeMultiplier": "0x20ccac8", "?GetArmorKind@@YAHPEAVTESObjectARMO@@@Z": "0x27edf0"}`
(decorated or `Class::member` names). Never edit `symbols.json` or `task.json`, and never give an
RVA the pack does not list. `decorated name changed` means a declaration change (for example
`struct` vs `class`, `const`, a parameter type) renamed a function; check that it was intended.
A thread-local (the target reads `gs:[0x58]` indexed by `_tls_index`, then adds a constant offset)
is `extern __declspec(thread) T name;` in your source, bound with `{"<decorated name>":
"tls:0x<offset the target adds>"}` (`UNBOUND thread-local` asks for it); `_tls_index` needs no hint.

**Source rules** (`python3 tools/check.py` runs the lint; a Reviewer rejects the rest):
- Plausible C++ for what the function does. Not allowed anywhere in a file, comments included:
  inline asm (`asm`, `__asm`, `__asm__`), `__emit`, `__pragma`/`_Pragma`, `##`, digit separators
  (`1'000`), byte arrays or `\x` strings, `\u`/`\U` escapes, `#pragma` other than
  `once`/`pack`/`warning`, `__declspec(naked|code_seg|allocate|safebuffers)` or a `#define`
  naming any of these. No dead code or odd control flow only to force bytes; justify anything
  unusual in a comment.
- `__forceinline`, `[[msvc::...]]` attributes and codegen intrinsics (`_BitScanForward`,
  `_Interlocked*`, `__assume`, `_mm_*`, ...) only with a justification comment of a few words on
  the same or the previous line, saying why a programmer would have written it
  (`// hot path: the engine inlines this accessor everywhere`). The lint checks that the comment
  is there; the Reviewer rejects a justification that is only "to match".
- One class per `reconstruction/<area>/<Class>.{h,cpp}`; the area follows the rule in
  `reconstruction/README.md` (`Ni*` netimmerse, `BS*` bsengine, `TES*`/`BGS*` forms, actor
  classes actors, or the owning system your brief names). The .cpp includes its header as
  `#include "<Class>.h"`.
- Other classes the function uses may be declared in your header as minimal stand-ins (only the
  members and virtual slots the code needs). Say in the header comment which declarations are
  stand-ins and where each name comes from. Do not edit another unit to share a class.
- Include lines are exactly `#include "path"` or `#include <system>` with nothing else on the line;
  never `#` and `include` together in a comment or string; no include inside `/* */` or `#if`
  (header guard aside); repository headers quoted. `attempt` refuses a unit whose compiler include
  list differs from the derived closure.
- Header comment of each file: build id and `Source exposure: <black-box|community-headers|binary-analysis|mixed>`.
  The .cpp adds `RVA 0x<rva>` and `<n> bytes` per compared function, `Evidence:`, `Drafted by <model>`,
  `Recipe: reconstruction/recipes/<name>.json` and which functions are compared. For `Evidence:`
  cite the `findings/` file your brief names for the function (the one its inventory entry cites);
  never cite a `reports/` path that does not exist yet. The match record is linked from the
  inventory later, so the source never has to change when it is written.
  Put `Labels: v2` in the leading comment of both files and label names only on lines of this
  form (the lint enforces it in v2 files):
  `// <names>: <LABEL> [<LABEL>...][; note]`, LABEL one of
  `COMMUNITY(<owner>/<repo>@<rev>, <licence>)` (e.g. `COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)`),
  `SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence)` (a name or declaration taken from the
  Fallout: New Vegas decompilation, below), `GUESS` or `GUESS(low|medium|high)`, `EXE_RTTI`,
  `OBSERVED`, and `STANDIN` together with the name's origin (`// TESObjectARMO: STANDIN COMMUNITY(...)`).
  A community name is `COMMUNITY` and an FNV name `SIBLING`, never `GUESS`; `GUESS` is only for
  names you made up. Do not write the label words anywhere else.
- **Sibling source (FNV).** `.local/sources/fnv_decomp` (momusdigital/fnv_decomp at `91e1b6e8`)
  may be read and reused by maintainer decision (`docs/authorizations.md`); its LICENSE grants
  none, so label everything you take. Before drafting, open the file and line your pack's
  "Sibling source" section gives for the same-named method and for the class's accessors and
  helpers. Adapt, do not assume: it is a 32-bit build of an older engine, most game units there
  are `/Od`, and its layouts, offsets and vtable slots do not carry over, so take shapes and
  names, then check every offset against your listing. If your unit reuses a body or a
  substantial part of one, add `// Sibling source: momusdigital/fnv_decomp@91e1b6e8 <path>:<line>`
  to the header comment (one line per body). `check_labels.py` verifies `SIBLING` names and the
  path; the Reviewer rejects undeclared reuse.
- **Search before you label.** The pinned community checkouts are local clones:
  `.local/sources/CommonLibSSE-NG` (CharmedBaryon/CommonLibSSE-NG at `b93280e`, MIT) and
  `.local/sources/CommonLibSSE-po3` (powerof3/CommonLibSSE at `654e55f`, GPL-3.0; a file using
  its names states GPL-3.0 in its header), and `.local/sources/AddressLibraryDatabase`
  (meh321/AddressLibraryDatabase at `0379cb6`, its `skyrimae.rename` name list; no licence file,
  used with the author's permission as reported by the maintainer, `docs/authorizations.md`;
  label `COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)`). Before giving any class, member, method, enum or
  enumerator a name, search them (`grep -rn '<name or offset>' .local/sources/CommonLibSSE-NG/include`)
  for the class and the member at that place (offset, virtual slot, bit range, value; NG's
  offsets are SE ones, so check how this build differs). If the community has a name there, use
  that exact spelling, its enumerator values and its accessor style (for example NG's
  `GetKnockState()` or `IsSneaking()` returning `static_cast<bool>(bitfield)`) and label it
  `COMMUNITY`; a base class modelled as a member is `STANDIN` plus the origin of its name. Only
  where the community has nothing do you invent a name and label it `GUESS`. When your
  declaration has to differ from the community one (a return type, a field width), keep the
  community name and say why in the note, for example `COMMUNITY(...) OBSERVED; NG declares double`.
- Before you finish, run `python3 tools/check_labels.py reconstruction/<area>/<Class>.h
  reconstruction/<area>/<Class>.cpp` (also printed by `attempt` as `label warning:` lines). It
  checks every `COMMUNITY` name and enumerator value against the pinned checkout and every
  `SIBLING` name against the FNV clone, flags `GUESS` names either declares in that class, and checks that each `Evidence:` file exists, is
  tracked, and names the unit (its class, a `// Task: <task-id>` header line, or every compared
  RVA). Fix each warning or explain it in your result line.
- Before you draft, read `docs/matching-cookbook.md` once. A flag bit the target tests as a load,
  `shr`, `test al,1` goes through a by-value bit-index helper (rule 16) from the first draft.
- No decompiler output pasted as source, no code from unlicensed projects other than the FNV
  decompilation (labelled as above), nothing leaked. Unknowns stay unknown (`unk28`), not
  invented names.

**Budget.** The budget is what `attempt` prints (`counted N/M`); it refuses past it (exit 5).
Stop work on a function after three counted attempts with no progress on its first mismatch
offset. If the only difference is a compiler-mode artefact (for example a parity branch `jp`
after `ucomiss`, which `/fp:fast` omits), stop and report it as the blocker: recipes are not
yours to change. **Never** edit tools/, reports/, data/, recipes or another unit, mark anything
`matched`, commit, push, post, start agents or drive Boat by hand.

**When a function is stuck**, take it out of the unit so the rest still passes, but never lose
it: save the function, and any header lines only it needs, to
`.local/tasks/<task-id>/near-miss/<rva>.cpp`, starting with two comment lines: the reason code,
sizes and attempt number of the best try, then the remaining difference in a sentence. Run
`attempt` once more to show the remaining functions pass, and name the file in your result line.

**At the end** write JSON lines only, one per function and one for the task, to
`.local/handoffs/<task-id>.jsonl`, and return the same lines:

```json
{"rva": "0x73ad90", "result": "pass", "reason": "all-checks-passed", "attempts": 3}
{"task": "<task-id>", "unit": "reconstruction/<area>/<Class>.cpp", "attempts": 3, "blocker": null}
```
