// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica45f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica45f0;
extern void construct(Statica45f0*, const Descriptor*);
extern void destroy(Statica45f0*);
struct Statica45f0 {
    void* value;
    Statica45f0() { construct(this, &descriptor); }
    ~Statica45f0() { destroy(this); }
};
