# Source reconstruction

Reconstructed source for functions that have a match record under `reports/`. A byte match does
not settle copyright status, and it does not verify a function's name or show what the original
source looked like. Each function's provenance is checked by a Reviewer subagent under the
acceptance rule in `docs/verification.md`, with provenance or legal doubt escalated. The
maintainer has decided that reconstructed source is published in this repository, organized by
engine area as below, in the same manner as the FNV decompilation project publishes its
reconstruction (`LEGAL.md`, "Publication of reconstructed source"). Changes to the matching gate
follow the acceptance rule's machinery-change path. Source is pushed only together with its
acceptance (`CONTRIBUTING.md`, "Publication"); a branch that holds integrated source still
awaiting a Reviewer approve stays local.
Do not copy FNV code, raw decompiler output, proprietary middleware or unlicensed implementations.
Read `LEGAL.md`, `PROVENANCE.md` and `docs/verification.md` before adding source.

## Layout

- **One pair per class**: `reconstruction/<area>/<Class>.cpp` holds the class's reconstructed
  member functions, and `reconstruction/<area>/<Class>.h` beside it the type declarations they
  need. The .cpp includes its header by a quoted name, so the unit compiles from the repository
  root with the recipe's flags and no include path. Every repository file a unit reaches through
  quoted includes belongs to its match record's translation unit; `tools/check.py` derives that
  set and rejects a record that omits or adds a file (`docs/verification.md`, "Match gate"). This stays the rule until the original
  translation units are evidenced (for example by RTTI or layout showing which classes shared an
  object); then a unit may hold several classes, as that evidence shows.
- **`<area>`** is the engine area that community headers make evident for the class, such as
  its base class or owning system (`inventory/` for the `InventoryChanges` item visitors). Use
  lowercase. When no area is evident, use `misc/` rather than guessing.
- **One recipe per source unit.** A match record binds a translation unit to one recipe in
  `recipes/<compiler>-<flags>.json` (compiler binary hash and version, flags, SDK, host). If a
  class's functions need different recipes, split them into separate units, one per recipe,
  instead of mixing flags. Never edit a recipe that a record names; add one.
- **Middleware stays apart.** Code identified as third-party middleware is not mixed into game
  classes' units; it needs its own area and its own provenance and licence assessment.
- Paths are build-independent. The build id lives in the match record and the inventory, not in
  the path. A class whose source differs between builds would need a reviewed layout extension.

The translation unit's identity is `tools/source_digest.py`: a SHA-256 over every file of the unit
with its path. That digest is the `source_revision` the comparator task, build record and report
carry, the digest a Reviewer record binds, and what `tools/check.py` recomputes from these files
for every entry that names a match record.

## Header of each file

State the build id, RVA and size of each compared function, the evidence path, the source exposure
(`PROVENANCE.md` categories), the model or person who drafted it, and which community
definitions, at which immutable revision and licence, informed the types. Label community names
as unverified. Say which functions in the unit are compared and which exist only to make it
compile. Comments explain why, never when or at whose request.

## Contents

| unit | function | build / RVA / size | record | state |
|---|---|---|---|---|
| `inventory/ArmorRatingVisitor` | `ArmorRatingVisitor::HaveNotVisitedArmor` (COMMUNITY name) | `sse-steam-1-7-104` / `0x73ad90` / 84 | `reports/sse-steam-1-7-104/0x73ad90.json` | accepted (`matched`) |
