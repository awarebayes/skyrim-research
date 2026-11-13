// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica32f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica32f0;
extern void construct(Statica32f0*, const Descriptor*);
extern void destroy(Statica32f0*);
struct Statica32f0 {
    void* value;
    Statica32f0() { construct(this, &descriptor); }
    ~Statica32f0() { destroy(this); }
};
