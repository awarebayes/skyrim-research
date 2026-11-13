// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica68f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica68f0;
extern void construct(Statica68f0*, const Descriptor*);
extern void destroy(Statica68f0*);
struct Statica68f0 {
    void* value;
    Statica68f0() { construct(this, &descriptor); }
    ~Statica68f0() { destroy(this); }
};
