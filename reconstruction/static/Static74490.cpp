// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: binary-analysis; possible sibling implementation exposure disclosed below.
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/staging/blk_00cc0000_o2.cpp:13192 (ContextScope helper).
// ContextScope lineage is uncertain; conservatively treated as adapted from that sibling source.
// ContextScope: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); no licence is granted by its authors.
// Its README attributes some names to an Xbox 360 development-build PDB and Havok/Gamebryo source.
// Reuse is under the maintainer decision in LEGAL.md, not this repository's MIT licence.
// Sibling material is not evidence about this target's names, addresses or behaviour.
// Drafted by GPT-6.1 Sol (recipe and generator).
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Only the generated initializer and its EH cleanup funclets are compared; the registered teardown is a reference binding.
// Labels: v2
// RVA 0x74490; 106 bytes
// object: GUESS(low) STANDIN
// Origin: {"family": "static-context-resource-initializer", "template_digest": "666632903df78a25abb6b73a9d6c9987130ce98fa1b3376462bbbc5788f6fd6b", "version": "2"}
#include "Static74490.h"
static Static74490 object;
