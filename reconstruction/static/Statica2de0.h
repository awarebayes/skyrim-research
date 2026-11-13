// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2de0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2de0;
extern void construct(Statica2de0*, const Descriptor*);
extern void destroy(Statica2de0*);
struct Statica2de0 {
    void* value;
    Statica2de0() { construct(this, &descriptor); }
    ~Statica2de0() { destroy(this); }
};
