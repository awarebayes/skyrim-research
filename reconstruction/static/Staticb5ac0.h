// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5ac0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5ac0;
extern void construct(Staticb5ac0*, const Descriptor*);
extern void destroy(Staticb5ac0*);
struct Staticb5ac0 {
    void* value;
    Staticb5ac0() { construct(this, &descriptor); }
    ~Staticb5ac0() { destroy(this); }
};
