// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2ff0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2ff0;
extern void construct(Statica2ff0*, const Descriptor*);
extern void destroy(Statica2ff0*);
struct Statica2ff0 {
    void* value;
    Statica2ff0() { construct(this, &descriptor); }
    ~Statica2ff0() { destroy(this); }
};
