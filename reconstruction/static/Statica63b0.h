// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica63b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica63b0;
extern void construct(Statica63b0*, const Descriptor*);
extern void destroy(Statica63b0*);
struct Statica63b0 {
    void* value;
    Statica63b0() { construct(this, &descriptor); }
    ~Statica63b0() { destroy(this); }
};
