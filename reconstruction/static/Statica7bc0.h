// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica7bc0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica7bc0;
extern void construct(Statica7bc0*, const Descriptor*);
extern void destroy(Statica7bc0*);
struct Statica7bc0 {
    void* value;
    Statica7bc0() { construct(this, &descriptor); }
    ~Statica7bc0() { destroy(this); }
};
