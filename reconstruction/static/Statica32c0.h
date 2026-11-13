// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica32c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica32c0;
extern void construct(Statica32c0*, const Descriptor*);
extern void destroy(Statica32c0*);
struct Statica32c0 {
    void* value;
    Statica32c0() { construct(this, &descriptor); }
    ~Statica32c0() { destroy(this); }
};
