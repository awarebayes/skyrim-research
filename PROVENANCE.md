# Provenance and source review

Every finding, specification, recovered name/layout or reconstructed function records:

- Target build id and image SHA-256; addresses as RVA, including the image base when discussing VA.
- Author/human operator, date, and AI model/tool where relevant (use `unknown` when unavailable).
- Exact source URLs and immutable revisions; license or `no license grant` for external material.
- Exposure category: `black-box`, `community-headers`, `binary-analysis`, or `mixed`.
- Method, observations, inference, confidence (`low`, `medium`, `high`) and unresolved alternatives.
- Reproduction instructions with local placeholders, sanitized evidence paths and reviewer.

Record a name's origin as `EXE_RTTI`, `COMMUNITY`, `SIBLING`, `OBSERVED`, or `GUESS`, with build
id and RVA. `SIBLING` marks a name, declaration or code taken from the FNV decompilation under the
maintainer decision in `docs/authorizations.md`; it describes another game's reconstruction, never
evidence about this build.
These tags are descriptions of evidence, not licenses. GUESS needs a confidence and rationale.
A header's size assertion proves only the tested property, not every offset or behavior.

Use `findings/TEMPLATE.md` and `specs/TEMPLATE.md`. Public evidence contains summaries and
metadata, never byte dumps or raw game-derived exports. Keep the originals locally and disclose
when a reviewer could not independently reproduce a claim. Preserve failed experiments.

## External sources

`SOURCES.md` records references used during bootstrap. Before importing anything, pin its
revision, inspect the license at that revision, retain notices and record exactly what was used.
`momusdigital/fnv_decomp` at `91e1b6e8` is the one unlicensed source the maintainer has allowed
for reuse (names, declarations and code in reconstructions; `docs/authorizations.md`, Notes): its
`LICENSE` grants no licence and its README tags some names as from an Xbox 360 development-build
PDB and from Havok/Gamebryo source. Label what is taken `SIBLING(...)`, cite a reused body in the
unit header, and do not vendor its tree or website assets wholesale. Apart from that decision, do
not import leaked/proprietary symbols or middleware source, and never obtain them yourself. The
presence of a type in an external archive is not proof of its provenance.
If a source is questionable, stop using it for publication and ask the maintainer to review;
do not paste questionable material into the issue used to discuss it.

## Boundary review

Binary-analysis notes and reconstructed implementations are exposure-bearing research.
Prose can still expose implementation details. `specs/` does not automatically mean clean-room
approved; each document needs review and an exposure declaration. Never automatically sync this
repo into Mudcrab. See `docs/clean-room.md`.
