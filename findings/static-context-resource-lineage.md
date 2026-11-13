# Static context/resource initializer lineage

Target: `sse-steam-1-7-104`, image SHA-256
`846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`.
Method and exposure: binary analysis and comparison with sibling reconstructed source.
Human owner: awarebayes. Tooling and disclosure correction: GPT-6.1 Sol.

The version-1 static resource template stated that no external implementation source was
reused. The original local recipe notes also described independent derivation. A subsequent
origin check found a close `ContextScope` destructor in
`momusdigital/fnv_decomp@91e1b6e8`, `src/staging/blk_00cc0000_o2.cpp:13192`.
Similarity does not establish copying, and the historical derivation cannot be independently
attested here. The version-2 initializer template therefore conservatively treats this helper
as adapted sibling material and discloses possible sibling implementation exposure. This
supersedes the independence claim for this family; it does not rewrite the earlier evidence.

Origin: `SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence)`. That project's authors grant
no licence. Its README attributes some names to an Xbox 360 development-build PDB and
Havok/Gamebryo source. Reuse follows the maintainer decision in `LEGAL.md` and
`docs/authorizations.md`; it is not covered by this repository's MIT licence. Every generated
unit carries the sibling source citation and notice. The other object and manager names remain
stand-ins with labelled low-confidence guesses. Sibling similarity establishes no Skyrim
name, layout, address, or behavior, and this research is not a clean-room transfer.

The template and extraction source are versioned separately from the earlier teardown family.
A changed template digest requires all members to be confirmed again on both runner hosts and
a fresh family/first-20 review. Exact-row audit coverage is a deterministic binding check,
not independent target extraction or a provenance verdict. No acceptance is claimed by this
note; current acceptance evidence is in the family manifests and per-function records.
