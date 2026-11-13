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
// Static6f790, Manager, manager, reserved, construct, release, value: GUESS(low) STANDIN
#pragma once
struct Static6f790;
struct Manager {
    virtual void reserved();
    virtual void construct(Static6f790*);
    virtual void release(Static6f790*);
};
extern Manager* manager();
// current_context, previous, Storage: GUESS(low) STANDIN
// ContextScope: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence)
// Thread-local storage models a separate context selection for each thread.
extern __declspec(thread) int current_context;
struct ContextScope {
    int previous;
    ContextScope() : previous(current_context) { current_context = 102; }
    ~ContextScope() { current_context = previous; }
};
struct Storage { void* value; ~Storage(); };
struct Static6f790 {
    Storage value;
    Static6f790() { ContextScope scope; manager()->construct(this); }
    ~Static6f790();
};
