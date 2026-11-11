# Legal, rights and publication policy

Maintainer: [awarebayes](https://github.com/awarebayes). Effective 2026-11-11.

## Purpose and independence

Independent research into Skyrim Special Edition for understanding, interoperability and
preservation. No affiliation, sponsorship or endorsement by Bethesda, ZeniMax, Microsoft or
middleware vendors is claimed. Game names and marks identify the subject only; ownership
remains with their holders. No proprietary logos, artwork or branding are used by this project.

The repository contains original infrastructure and documentation and, under `reconstruction/`,
reconstructed source for individual functions as described below. This policy is a contribution
rule, not a legal opinion or guarantee.

## Inputs and prohibited publication

Researchers must have a legally obtained copy and comply with relevant law and agreements.
Keep proprietary inputs and all raw game-derived analysis private under `.local/`.
Do not distribute executables (original, modified or rebuilt), binary sections, machine-code
listings, raw disassembly/decompiler exports, object files, libraries, memory dumps, save files,
assets, extracted data tables, PDBs, proprietary SDKs or compiler packages through this project.
This includes Git history, LFS, issues, comments, screenshots, releases, logs and CI artifacts.

Do not acquire or use leaked/confidential source, unofficial proprietary debug symbols or
unlawfully obtained development material. Do not assume a public URL establishes authorization.
No copy-protection removal tools or instructions belong here. A reference link is not adoption
of the linked project's practices or a license to reproduce its contents.

## Research publication and source reconstruction

Original tooling, factual metadata, reviewed explanations and synthetic fixtures are public
outputs.

**Publication of reconstructed source: maintainer decision.** The maintainer (awarebayes) has
decided that reconstructed source is published in this repository, in the same manner as the FNV
decompilation project publishes its reconstruction: as source files in the public repository,
organized by engine area (`reconstruction/<area>/`, see `reconstruction/README.md`). This records
the maintainer's policy decision; it is not a legal opinion, and no further conclusion is drawn
from it here. It changes no other rule in this file or in `PROVENANCE.md`: only reconstructed
source and its sanitized records are published, never game files, binary bytes, disassembly,
decompiler output, objects, or leaked, proprietary or unlicensed material, and no FNV code is
copied. Following FNV's manner of publication is not a licence to reuse FNV's material.

Each function is published only once accepted under the acceptance rule in
`docs/verification.md`, which includes a per-function provenance review by a Reviewer subagent,
with provenance or legal doubt escalated to the maintainer. The copyright status of reconstructed
implementations is not settled by matching bytes or withholding binaries.
Nothing in this repository grants third-party rights. See `LICENSE` for the narrow infrastructure
license; do not label the entire repository MIT or copy FNV code, which has no license grant.
Contributor authorship alone does not establish rights to all underlying material.

US law distinguishes ideas/methods from protected expression in [17 USC 102(b)](https://www.law.cornell.edu/uscode/text/17/102).
The interoperability provisions of [17 USC 1201(f)](https://www.law.cornell.edu/uscode/text/17/1201)
have conditions and are not a blanket permission to circumvent, copy or redistribute. Other
jurisdictions and agreements may differ. A disclaimer, lawful purchase or separate repository
alone does not establish compliance. Seek qualified advice for uncertain publication decisions.

## Contributor responsibility and automated work

Submit only work you have authority to contribute, identify external sources and applicable
licenses, and disclose relevant source exposure and AI assistance. Human operators are responsible
for agent submissions. Tool output and AI-generated text need review; neither proves provenance,
correctness or legal compliance. Do not send proprietary inputs to cloud services merely because
an agent has network access. Follow `PROVENANCE.md` and `docs/clean-room.md`.

## Concerns and reports

Rights holders should contact [the maintainer](https://github.com/awarebayes), identifying the
specific path or URL, claimed rights and requested action. For an ordinary public report,
open an issue with metadata only. For confidential concerns, use an available private contact
route on that profile; do not post the confidential content to this repository. Do not attach
binaries, dumps, proprietary source or credentials. The maintainer will investigate and can
restrict or remove disputed material. This does not promise a legal outcome or response deadline.

The original infrastructure is provided without warranty under its scoped MIT license. No
warranty is made that research is accurate, complete, safe for saves, or suitable for gameplay.
