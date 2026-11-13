// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2ac0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2ac0;
extern void construct(Statica2ac0*, const Descriptor*);
extern void destroy(Statica2ac0*);
struct Statica2ac0 {
    void* value;
    Statica2ac0() { construct(this, &descriptor); }
    ~Statica2ac0() { destroy(this); }
};
