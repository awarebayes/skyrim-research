// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica05f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica05f0;
extern void construct(Statica05f0*, const Descriptor*);
extern void destroy(Statica05f0*);
struct Statica05f0 {
    void* value;
    Statica05f0() { construct(this, &descriptor); }
    ~Statica05f0() { destroy(this); }
};
