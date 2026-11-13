// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21ac0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21ac0;
extern void construct(Static21ac0*, const Descriptor*);
extern void destroy(Static21ac0*);
struct Static21ac0 {
    void* value;
    Static21ac0() { construct(this, &descriptor); }
    ~Static21ac0() { destroy(this); }
};
