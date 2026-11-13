# Resource and technique guidelines for agents

Build `sse-steam-1-7-104` (image SHA-256 `846efccf…f1402f`, re-hashed for this work). Which source
or technique to use for which kind of function, how to check a source against the pinned image
first, and which structural shortcuts are worth building. Extends `findings/community-resources.md`
("the survey"), which holds the resource table and licences. Task `p5-resource-guidelines`,
Engineer worker (claude-fable-5-2), 2026-11-12, one host, not reviewed.

**Evidence labels.** *Measured* = counted here on the pinned image with original stdlib scripts
(private, `.local/experiments/resource-guidelines/`), using the Ghidra export of 176,001 function
entries from `findings/ghidra-import.md`, the image's own POGO, RTTI, `.pdata` and relocation
data, and a local disassembly reduced to hashes. *Estimated* = derived by a stated heuristic.
Every yield below is a **potential** (how much code has a property), never a count of matches.
Community revisions: powerof3/CommonLibSSE `654e55f7` (GPL-3.0, "po3"),
CharmedBaryon/CommonLibSSE-NG `b93280e8` (MIT, "NG").

## 1. Decision table

Use the first source that passes its check (section 2). Labels are the `Labels: v2` forms of
`docs/drafter-card.md`. "Skeleton" and "stamp" are the procedures of section 3.

| kind of function or class | names | types, layout, slots | technique, in order | label in source |
|---|---|---|---|---|
| virtual method of an RTTI class | class: image RTTI; method: NG slot comment, then po3 slot comment if the class passes checks C1 to C3 | NG header, then po3; size by C4, offsets by C5 | class unit, Drafter; exemplar from the same shape cluster in the brief | `EXE_RTTI` for the class; `COMMUNITY(<repo>@<rev>, MIT)` or `COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)` |
| deleting destructor, adjustor thunk, empty or constant-return virtual, other shape with 20 or more copies | class from RTTI; no method name needed | vftable from the image, size from C4 | skeleton, then stamp; no Drafter | `EXE_RTTI`, `OBSERVED` (size, slot) |
| non-virtual member with an Address Library id name | NG id name, then po3; `how: enclosing` names are hints | community header after C4 and C5 | class unit, Drafter | `COMMUNITY(...)`; `GUESS` if you rename |
| instantiation of a template (RTTI family, or same code with other targets) | template name from RTTI; members from community headers | one template definition | Drafter solves one instantiation; stamp the rest by explicit instantiation | as the row above |
| handler registered with a name (script native, console or script command) | the registration string in the image, after the table check | signature from the registering wrapper | ordinary Drafter task; the name is not community-derived | `OBSERVED` |
| unnamed function, no id, not in a vftable | none: `unk`/`GUESS`; address neighbourhood is a hint only | observed displacements only | Drafter, after its most-called callees are accepted | `GUESS(low)` |
| dynamic initializer or atexit destructor (`.text$di`, `.text$yd`) | variable names are guesses | type from the constructor it calls | not a Drafter task: generator, once the comparator supports these symbols | `GUESS`, `OBSERVED` |
| function with a C++ exception handler | as its kind above | as its kind above | contract v2; funclets are never separate tasks; larger attempt budget | as its kind |
| record load/save, plugin or save format code | enum and flag meaning from xEdit or UESP as facts | never memory layout from a file format | Drafter; cite as reference | `GUESS` with the citation in the note |
| Havok, Scaleform, Bethesda.net client, CRT/STL, import thunks | n/a | n/a | out of scope: do not draft, do not count | n/a |
| zlib 1.2.7, libpng 1.2.18 | upstream names | upstream source | parked: section 3, "not adopted" | upstream licence notice |

Compiler-generated static initialisers and teardowns are included regardless of middleware ownership under the delegated decision in `docs/authorizations.md`; priorities for handwritten middleware code are unchanged.

## 2. Rules per approved source

**Checks to run before trusting a community class** (all are local, model-free and take
milliseconds; the exporter should run them and write the outcome into `class.json`):

- **C1 length.** Highest declared slot + 1 must not exceed the image vftable length.
- **C2 range.** Every `override` slot is below the parent's image vftable length; every new
  `virtual` slot is at or above it. A parent that grew between game versions fails here.
- **C3 pattern.** An `override` slot holds a different pointer than the parent's vftable; an
  undeclared slot holds the same pointer. Many failures in one class mean a shifted numbering.
- **C4 size.** `sizeof` in the header equals the size argument the image passes to `operator
  delete` in that class's scalar deleting destructor.
- **C5 offsets.** Each member a function uses matches a displacement in the pack's "Observed
  memory operands". A `static_assert(sizeof)` proves the size only (`PROVENANCE.md`).

Measured for po3 on the pinned image: of 928 classes with a checkable parent, 636 pass C1 to C3
cleanly, 138 have C3 deviations only, **154 (17%) fail C1 or C2**; the survey reported 35 from C1
alone. Slot level: 138 of 1,209 new-virtual declarations lie inside the parent's vftable, 69
declarations lie past the end, 159 of 4,760 overrides equal the parent's pointer, 276 of 18,646
undeclared slots differ. Dropping the 154 classes removes 620 of the 14,227 joined names. C4: the
size is readable for 7,115 of 7,390 primary-vftable classes; where po3 also asserts a size
(1,174 classes) they agree in **1,160 (98.8%)** and differ in 14. Some C2 failures may be headers
that simplify the hierarchy rather than wrong slots; either way the class needs an Engineer look
before its slot names are used.

- **CharmedBaryon/CommonLibSSE-NG (MIT).** First choice for every name, declaration and excerpt.
  Cite `COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)`. Its slot comments cover fewer
  classes (414 with slot comments against 1,137, survey), so most slot names come from po3.
- **powerof3/CommonLibSSE (GPL-3.0).** Approved for names and declarations, including in published
  sources (`docs/authorizations.md`). Use it only where NG has nothing, so GPL-derived text stays
  small; cite the full label on every name line; never paste comments, helper code or whole class
  bodies; packs keep its excerpts in `*.GPL-local-only.*` files. Slot names only for classes that
  pass C1 to C3. Attribute an inherited implementation to the most-base class whose vftable
  first holds that pointer, not to the derived class the join happened to visit.
- **Address Library 1.7.104.0.** Id/offset pairs may be published (approved). An id proves only
  that the address is the one the community tracks, not what the function does. Never carry an
  address or an id-derived name to another build without the database for that build.
- **The image's own RTTI.** Class names, hierarchy, vftable contents and lengths are the ground
  truth the community sources are checked against. Label `EXE_RTTI`. Publish names and counts,
  never tables of addresses beyond what a task needs.
- **The image's own registration data.** A name is `OBSERVED` only when it comes from a table or
  registration call whose record layout an Engineer has confirmed on at least 20 entries (name
  pointer and handler pointer at fixed positions). Proximity of a string to a pointer is not
  enough. Strings are game data: quote a name in source only where the function itself is named
  by it.
- **xEdit definitions (MPL-2.0), UESP (CC BY-SA 2.5).** Facts about file formats only, cited by
  URL and revision in the unit's header note. Do not copy text or tables; do not infer memory
  layout from a file layout. **objdiff, Ghidra FID:** local aids, never evidence.

## 3. Techniques, ranked by expected yield per unit of effort

Where the cost is (measured from `data/costs.json`, second batch, five functions): Engineer
preparation 1.5M cache-read tokens per function, Drafter 0.57M, Reviewer 0.08M. The exporter now
replaces most of the first; the Drafter loop is the remaining floor. Where the bytes are
(measured): 106,486 non-funclet, non-thunk entries hold 21.87 MB; functions over 512 bytes are
9,226 entries and 46.5% of those bytes; functions of 32 bytes or less are 17% of entries and 1%
of bytes. Techniques 1 to 3 remove a large share of *functions* from the Drafter queue for almost
no model effort; none of them shortens the large functions, where only technique 5 helps.

1. **Class skeletons from the image (Engineer tooling; no model per class).** For every RTTI
   class emit a private `class.json`: bases, vftable length, per-slot target and whether it equals
   the parent's, object size from C4, and C1 to C3 results for each community header. From it,
   generate header skeletons that compile the class's deleting destructor and trivial virtuals.
   Measured: 7,115 class sizes; 3,613 functions sit in slots po3 declares as destructors (338 KB);
   one function (the pure-virtual stub) fills 2,790 of 89,745 slots; no cross-hierarchy folding
   was found, so a slot name applies to one implementation.
2. **Solve one, stamp the cluster (Engineer tooling; then one Drafter solve per pattern).**
   Hash each function's instruction stream with relocation targets masked (L1) and additionally
   with immediates and displacements masked (L2); keep the table private. Give the Drafter one
   representative per cluster; a script then instantiates the accepted source for each member with
   its class, targets and constants read from the image, and submits it to the verifier.
   Measured: identical code is **not** folded in this image (9,596 `.text$mn` functions are
   byte-for-byte copies of another, in 1,086 groups). In `.text$mn` (90,146 entries, 20.49 MB),
   34,433 entries and 2.85 MB (13.9%) repeat an L1 pattern already present; 229 patterns with 20
   or more members cover 22,950 entries and 1.41 MB. Of 17,608 entries of 32 bytes or less, 100
   L2 shapes cover 12,738. Template classes: 4,184 RTTI instantiations in 215 families (73
   families with 10 or more cover 3,848); their 7,695 own virtual functions reduce to 2,173 L1
   patterns. Estimated cost: a pattern costs one normal function; members cost verifier seconds.
   Risk: stamped members need a real class identity to be plausible C++, so stamp only members
   reachable from a vftable or already named; the rest wait.
3. **Static initializers and atexit destructors (comparator change plus generator).**
   The image's POGO record separates them exactly (measured): `.text$di` 9,762 entries, 916 KB;
   `.text$yd` 6,508 entries, 437 KB; together 6.2% of non-funclet bytes. The CRT initializer table
   lists **11,208** initializers, so the Ghidra export misses 1,446 of them. They are 93% L1
   repeats; 35 L2 shapes cover 15,524 of the 16,270 exported. Each follows from one global
   definition, but the symbols are static and not in their own COMDAT, which contract v2 refuses.
   Do this after 1 and 2: it is worth 6% of bytes, needs a contract change with its own review, and
   needs the maintainer's answer to question 3 in section 6.
4. **Order work by fan-in (planner change, hours).** Measured: 415,325 direct call or jump sites
   target function entries; the 1,000 most-referenced entries take 62.8% of them; 2,880 entries
   have 10 or more distinct callers and 1,097 of those are 64 bytes or less. Draft these first:
   every accepted callee turns an "unnamed target" in its callers' packs into a verified
   declaration (return and parameter types change the caller's code), and its body is the
   reference when a caller shows the same instructions inlined.
5. **Verified shared headers and exemplars (process change).** Per-unit stand-ins make every
   Drafter rediscover the same layout. An Engineer integration step promotes a class to one shared
   header once a function using it is accepted, with C4 as a `static_assert` and the offsets that
   accepted functions exercised marked verified. Each brief names the accepted unit closest in L2
   shape as an exemplar. Yield not measured; compare attempts per function with the third batch.
6. **Names from registration data (Engineer tooling).** Measured upper bounds by a proximity
   heuristic, unverified: 1,649 functions are pointed to from non-vftable data next to a string
   pointer (387 KB) and 1,383 have their address taken in code right after a string (283 KB).
   Expect fewer after the per-table check of section 2. Value: names with no licence question.

**Not adopted, with reasons.**

- **A function-to-translation-unit map; unit-level builds instead of function-level matching.**
  The three signals anchor few units: 121 anonymous-namespace hashes (72 shared by two or more
  types, 456 types in all) and about 49 non-middleware source-path strings (survey), against 2,409
  C++ objects of the pinned compiler in the Rich header. Link order is only loosely shared between
  sections (measured): vftable order follows code order for 78% of adjacent classes (longest
  increasing run 69.5%); the initializer table and `.text$di` agree for 60% of adjacent pairs. A
  class's address span predicted the community class name of an enclosed function in 25 of 43
  checked cases at a 4 KiB gap. Use adjacency to batch neighbours into one task, label any class
  guess from it `GUESS(low)`, and keep per-function comparison: with function-level COMDATs it
  does not depend on unit composition.
- **zlib/libpng from upstream now.** Their address spans hold about 39 and 214 entries, 105 KB
  together, under 0.5% of bytes (estimated from functions that reference their message strings).
  The Rich header has only 6 C objects from the pinned compiler build and 41 from other builds
  (`findings/compiler-candidates.md`), so they were very probably not built by the pinned recipe.
  Matching them needs another toolset and recipe for half a percent of the bytes. Park it.
- **Comparator as an oracle for signature or layout variants.** C1 to C5 answer the same questions
  without a compile; a variant sweep costs Boat time and invites byte-forcing.
- **Mining inlined bodies to recover helpers.** No cheap detector; technique 4 finds the same
  helpers by doing callees first.

**Corrections to the survey.**

- *Vtable join.* "About 14,200 named functions" is a count of entries, names unverified. Measured
  breakdown (overlapping): 3,613 are deleting destructors, 4,152 are under 16 bytes, 2,387 are
  inherited implementations seen through several classes; **6,317 have code found nowhere else**.
- *Exception funclets.* 67,896 funclets are 38% of entries and 4% of bytes, as stated, and the
  POGO `.text$x` range confirms the count. That is a change of denominator, not of work. The work
  fact is the reverse: **39,848 functions (37.4%) holding 11.68 MB (53% of non-funclet bytes) have
  a language handler**, with 95,395 unwind-map entries and 714 try blocks. Contract v2 is therefore
  required for half the code, and those functions cost more to match because destruction order
  and temporaries must also agree.
- *Scope.* The upper bound of 95,000 counted initializer and teardown code as game code: 13,512 of
  the 18,911 "unlabelled window" functions lie in `.text$di`/`.text$yd`. Re-estimated by nearest
  labelled neighbour in `.text$mn`: 68,000 to 78,000 ordinary game functions holding 15.4 to 17.2
  MB (the upper end counts `std`-labelled neighbourhoods as game code), plus about 17,700 generated
  initializer and teardown functions. Scaleform has almost no RTTI and is still undercounted, so
  the lower end is the better guess.
- *Folding.* The survey's "likely folded stubs" are not folds; see technique 2.

## 4. Excluded

- **meh321's rename file** (no licence), **skse64** (no grant), **Fallout 3 decompilation**
  (no source published): nothing from them in tracked files or briefs; study of method only. The
  **FNV decompilation** is no longer excluded: the maintainer allowed its names, declarations and
  code in reconstructions, labelled `SIBLING(...)` (`docs/authorizations.md`, Notes).
- **alandtse/CommonLibSSE-NG, the VR address library's names, nif.xml**: not approved (the
  approval names powerof3 only); not a naming source until section 6 is answered.
- **Leaked source, unofficial PDBs, proprietary SDKs, middleware source**: never acquired, used
  or named (`LEGAL.md`).
- **Copying code** from a community header (inline helpers, wrappers, comments). Names,
  declarations, slot numbers and sizes are used; implementations are written from the image.
- **Decompiler output as source**, and any game-derived listing, hash or address table in a
  tracked file. The cluster and class tables of section 3 stay private.

## 5. Proposed pipeline changes, in priority order

1. **Exporter:** emit `class.json` with C1 to C4 for every RTTI class; refuse po3 slot names for a
   class that fails C1 or C2; attribute inherited slots to the defining class.
2. **Exporter and planner:** private L1/L2 cluster table; `plan` picks one representative per
   cluster, prefers high fan-in functions, and batches address-adjacent functions of one class.
3. **Stamping tool:** instantiate an accepted pattern for cluster members and run the verifier;
   members are accepted under the existing rule, with the Reviewer pass taken per batch on the
   pattern plus a random sample, as `docs/verification.md` already permits.
4. **Scope accounting:** progress in bytes; one unit is a function with its funclets; separate
   denominators for ordinary game code, generated initializer and teardown code, and excluded
   middleware; import the 1,446 initializers missing from the inventory source; no percentage
   until middleware is classified better than by neighbourhood.
5. **Cost accounting:** report tokens per accepted byte and per stage; charge a pattern's cost to
   all members of its cluster; record stamped members as a separate profile so projections do not
   mix them with drafted functions.
6. **Drafter card:** shared verified headers replace per-unit stand-ins for promoted classes; the
   brief carries an exemplar unit. **Comparator contract v3** (static functions in
   `.text$di`/`.text$yd`) only if question 3 is answered yes.

## 6. Open questions for the maintainer

1. **Licence of files that carry po3-derived declarations.** The approval covers use and labelling.
   Should such files state GPL-3.0 explicitly, given that `LICENSE` covers only the
   infrastructure?
2. **Ask meh321 for a licence** on the rename file? It is the largest naming source (14,604
   method names, survey) and cannot be used without one.
3. **Generated initializer units.** Accept machine-generated sources for the about 17,700
   initializer and teardown functions, many of which consist of a string literal from the image and
   a guessed variable name? It is 6% of bytes with little insight.
4. **alandtse/CommonLibSSE-NG and the VR address library names.** They add 205 id names and 2,104
   names of unrecorded origin (survey). Recommendation: decline both for now; the checks in
   section 2 make po3 sufficient.
5. **A second toolset for library code** (zlib, libpng): recommendation is to leave it out of scope.
