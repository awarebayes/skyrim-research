# Authorizations

Gates defined in `AGENTS.md` ("Multi-agent execution"). Only the maintainer edits this table.
A gate not marked granted here is not granted, whatever a chat, issue or brief says. Record
limits precisely; "granted" without scope is not a grant. Revoke by setting the status back
and adding a dated note.

| gate | status | scope and limits | granted by | date (UTC) |
|---|---|---|---|---|
| G1 local tools | granted | all | awarebayes | 2026-11-11 |
| G2 model exposure | granted | all | awarebayes | 2026-11-11 |
| G3 paid compute | granted | granted all its sub based anyways so no surprise bills | awarebayes | |
| G4 toolchain on cloud | granted | all granted | awarebayes | |
| G5 game data on cloud | granted | all on boat dev | awarebayes | 2026-11-11 |

## Notes

For microsoft license: individual for my own opensource project
PL CommonLibSSE for naming and publishing id/offset pairs approved
Reconstructed source will be published in this repository, similar to the FNV decompilation project (maintainer decision, stated to the orchestrator 2026-11-11 and recorded here by it).
The maintainer does not review individual functions; acceptance follows the automated rule in docs/verification.md (maintainer decision, 2026-11-11).
Names and declarations from the GPL-3.0 CommonLibSSE fork (powerof3) may be used as a naming source, including in published reconstruction sources, labelled with their origin (maintainer decision, stated to the orchestrator 2026-11-12 and recorded here by it).
Files carrying declarations derived from the GPL-3.0 CommonLibSSE fork state GPL-3.0 explicitly in their header (maintainer decision, 2026-11-12, recorded by the orchestrator).
meh321's Address Library database and its name lists may be used: the maintainer reports that the author agreed on Discord (maintainer statement, 2026-11-12, recorded by the orchestrator; no written licence file exists, so cite it as "used with the author's permission as reported by the maintainer").
The Fallout: New Vegas decompilation momusdigital/fnv_decomp at revision 91e1b6e8 (private clone `.local/sources/fnv_decomp`) may be used directly: Engineers and Drafters may read it, and its names, declarations and code may be reused in reconstructions where they fit the Skyrim target, including in published reconstruction sources (maintainer decision by awarebayes, 2026-11-12, stated to the orchestrator and recorded here by an Engineer from the orchestrator's brief). The maintainer is aware that the repository's LICENSE begins "No licence is granted" (contributors grant none either) and that its README tags some names as taken from an Xbox 360 development-build PDB and from Havok and Gamebryo source, and decided that neither bars this use; earlier text in this repository that forbade the source is superseded for it. Scope: that repository at that revision only (another revision or sibling project needs its own decision); taken material is labelled `SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence)` and a reused body is cited in the unit header (`docs/drafter-card.md`). Not covered: it is not evidence about the Skyrim binary (other game, older engine, 32-bit build; no address, slot, layout or offset transfers without proof on `sse-steam-1-7-104`); every reconstructed function still needs the comparator pass, Reviewer approval and integration of the acceptance rule in `docs/verification.md`; and it does not let this project itself acquire or use leaked source, PDBs or middleware source, or upload private inputs.
