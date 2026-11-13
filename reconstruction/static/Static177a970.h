// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: binary-analysis; no external implementation source reused.
// Drafted by GPT-6.1 Sol (recipe and generator).
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Only the generated teardown and its EH scope are compared; constructor and manager implementations are reference bindings.
// Labels: v2
// Static177a970, Manager, manager, reserved, construct, release, value: GUESS(low) STANDIN
#pragma once
struct Static177a970;
struct Manager {
    virtual void reserved();
    virtual void construct(Static177a970*);
    virtual void release(Static177a970*);
};
extern Manager* manager();
// empty_resource, cleanup: GUESS(low) STANDIN
extern unsigned char empty_resource;
extern void cleanup(Static177a970*);
struct Static177a970 {
    void* value;
    Static177a970();
    ~Static177a970() { value = &empty_resource; manager()->release(this); cleanup(this); }
};
