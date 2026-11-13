// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica27f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica27f0;
extern void construct(Statica27f0*, const Descriptor*);
extern void destroy(Statica27f0*);
struct Statica27f0 {
    void* value;
    Statica27f0() { construct(this, &descriptor); }
    ~Statica27f0() { destroy(this); }
};
