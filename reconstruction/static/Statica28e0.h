// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica28e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica28e0;
extern void construct(Statica28e0*, const Descriptor*);
extern void destroy(Statica28e0*);
struct Statica28e0 {
    void* value;
    Statica28e0() { construct(this, &descriptor); }
    ~Statica28e0() { destroy(this); }
};
