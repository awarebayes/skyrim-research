// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica48c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica48c0;
extern void construct(Statica48c0*, const Descriptor*);
extern void destroy(Statica48c0*);
struct Statica48c0 {
    void* value;
    Statica48c0() { construct(this, &descriptor); }
    ~Statica48c0() { destroy(this); }
};
