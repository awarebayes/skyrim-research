// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica30e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica30e0;
extern void construct(Statica30e0*, const Descriptor*);
extern void destroy(Statica30e0*);
struct Statica30e0 {
    void* value;
    Statica30e0() { construct(this, &descriptor); }
    ~Statica30e0() { destroy(this); }
};
