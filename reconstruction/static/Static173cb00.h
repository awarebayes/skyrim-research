// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: binary-analysis; no external implementation source reused.
// Drafted by GPT-6.1 Sol (recipe and generator).
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Only the generated teardown and its EH scope are compared; constructor and manager implementations are reference bindings.
// Labels: v2
// Static173cb00, Manager, manager, reserved, construct, release, value: GUESS(low) STANDIN
#pragma once
struct Static173cb00;
struct Manager {
    virtual void reserved();
    virtual void construct(Static173cb00*);
    virtual void release(Static173cb00*);
};
extern Manager* manager();
// empty_resource, cleanup: GUESS(low) STANDIN
extern unsigned char empty_resource;
extern void cleanup(Static173cb00*);
struct Static173cb00 {
    void* value;
    Static173cb00();
    ~Static173cb00() { value = &empty_resource; manager()->release(this); cleanup(this); }
};
