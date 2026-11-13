// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica64a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica64a0;
extern void construct(Statica64a0*, const Descriptor*);
extern void destroy(Statica64a0*);
struct Statica64a0 {
    void* value;
    Statica64a0() { construct(this, &descriptor); }
    ~Statica64a0() { destroy(this); }
};
