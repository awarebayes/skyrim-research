# Finding: four functions selected from existing shared units

Status: selection metadata only; no match or acceptance claim.
Author / human operator: awarebayes
AI assistance / model: gpt-6.1-sol, Engineer, task p85-shared-sync
Date (UTC): 2026-11-13
Target build id: `sse-steam-1-7-104`
Image SHA-256: `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Source exposure: mixed (local binary analysis and community declarations).
Sources: the pinned image; CharmedBaryon/CommonLibSSE-NG at
`b93280e832f263dbef44e44cbe2936622a02f91a` (MIT). Private drafting context may also
include the maintainer-authorized FNV decompilation `momusdigital/fnv_decomp@91e1b6e8`
(no licence grant); it is never evidence about the Skyrim image.
Name provenance: COMMUNITY, unverified. Confidence: medium for the names and class attribution;
function identities and lengths are the existing local export metadata pending deterministic confirmation.

The p68d selection extends units that already contain accepted functions. These four entries
were absent from the public inventory. Their existing task metadata supplies build, RVA, length
and community spelling; enrollment records them as mapped. Reproduction and review follow
`docs/verification.md`, including re-confirmation of every affected accepted function before a
changed shared unit is accepted. A local attempt pass alone makes no match claim.

Selected functions (RVA, machine-code size, unverified name):

- `0x539050`, 143 bytes: `BGSStoryManagerQuestNode::SaveGame`.
- `0x1e1380`, 420 bytes: `TESDescription::GetDescription`.
- `0x26b760`, 180 bytes: `TESEffectShader::InitItemImpl`.
- `0x3b7240`, 319 bytes: `TESIdleForm::InitItemImpl`.

Method: compare the selected task identities with the pinned target and the public inventory;
add only missing identities, retaining the existing lengths and names. The private task export,
function packs, journals and source backups remain local. No raw listings or bytes are published.
To check the public metadata, run `python3 tools/check.py`, the unit suite and
`python3 tools/build_site.py`. Those checks establish publication consistency, not a byte match,
name correctness, legal status, source equivalence or gameplay behavior.
