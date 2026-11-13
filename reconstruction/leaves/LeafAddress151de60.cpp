// Build: sse-steam-1-7-104; RVA 0x151de60; 8 bytes
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: binary-analysis; no external implementation reused.
// Drafted by GPT-6.1 Sol, census leaf population template.
// Labels: v2
// LeafAddress151de60, Address, leaf_target, leaf_global: GUESS(low) STANDIN
// Owning system and original signature are unknown; the class is an ABI stand-in.
// Only Address is compared. No original class, behavior or pointee type is claimed.
// Origin: {"family": "census-address-leaf", "template_digest": "b18016973b925d0755b2acaa7a6dc1f0e14b5df18c55cb1516affefe633c01bd", "version": "1"}
#include "LeafAddress151de60.h"
extern unsigned char leaf_global;
void* LeafAddress151de60::Address() { return &leaf_global; }
