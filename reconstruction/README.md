# Source reconstruction

Reconstructed source for functions that have a match record under `reports/`. Publishing a file
here is a maintainer provenance decision (`LEGAL.md`); a byte match does not settle copyright
status, and it does not verify a function's name or show what the original source looked like.
Do not copy FNV code, raw decompiler output, proprietary middleware or unlicensed implementations.
Read `LEGAL.md`, `PROVENANCE.md` and `docs/verification.md` before adding source. Provenance and
publication of each function are checked by a Reviewer subagent under the acceptance rule in
`docs/verification.md`; changes to the matching gate follow that rule's machinery-change path.

## Layout

- **One translation unit per class**: `reconstruction/<area>/<Class>.cpp` holds the class's
  reconstructed member functions, and `reconstruction/<area>/<Class>.h` beside it holds the type
  declarations they need. The .cpp includes its header by a quoted name, so the unit compiles
  from the repository root with the recipe's flags and no include path.
- **`<area>`** is the engine area that community headers make evident for the class, such as
  its base class or owning system (`inventory/` for the `InventoryChanges` item visitors). Use
  lowercase. When no area is evident, use `misc/` rather than guessing.
- **`recipes/<compiler>-<flags>.json`** are the compile recipes match records pin (compiler
  binary hash and version, flags, SDK, host). Never edit a recipe that a record names; add one.
- Paths are build-independent. The build id lives in the match record and the inventory, not in
  the path. A class whose source differs between builds would need a reviewed layout extension.

The translation unit's identity is `tools/source_digest.py`: a SHA-256 over every file of the unit
with its path. That digest is the `source_revision` the comparator task, build record and report
carry, and `tools/check.py` recomputes it from these files for every `matched` entry.

## Header of each file

State the build id, RVA and size of each compared function, the evidence path, the source exposure
(`PROVENANCE.md` categories), the model or person who drafted it, and which community
definitions, at which immutable revision and licence, informed the types. Label community names
as unverified. Say which functions in the unit are compared and which exist only to make it
compile. Comments explain why, never when or at whose request.

## Contents

| unit | function | build / RVA / size | record |
|---|---|---|---|
| `inventory/ArmorRatingVisitor` | `ArmorRatingVisitor::HaveNotVisitedArmor` (COMMUNITY name) | `sse-steam-1-7-104` / `0x73ad90` / 84 | `reports/sse-steam-1-7-104/0x73ad90.json` |
