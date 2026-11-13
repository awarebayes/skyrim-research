// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica45c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica45c0;
extern void construct(Statica45c0*, const Descriptor*);
extern void destroy(Statica45c0*);
struct Statica45c0 {
    void* value;
    Statica45c0() { construct(this, &descriptor); }
    ~Statica45c0() { destroy(this); }
};
