// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: binary-analysis; no external implementation source reused.
// Drafted by GPT-6.1 Sol (recipe and generator).
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Only the generated teardown and its EH scope are compared; constructor and manager implementations are reference bindings.
// Labels: v2
// Static1795f40, Manager, manager, reserved, construct, release, value: GUESS(low) STANDIN
#pragma once
struct Static1795f40;
struct Manager {
    virtual void reserved();
    virtual void construct(Static1795f40*);
    virtual void release(Static1795f40*);
};
extern Manager* manager();
// empty_resource, cleanup: GUESS(low) STANDIN
extern unsigned char empty_resource;
extern void cleanup(Static1795f40*);
struct Static1795f40 {
    void* value;
    Static1795f40();
    ~Static1795f40() { value = &empty_resource; manager()->release(this); cleanup(this); }
};
