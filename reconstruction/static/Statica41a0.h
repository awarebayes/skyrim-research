// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica41a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica41a0;
extern void construct(Statica41a0*, const Descriptor*);
extern void destroy(Statica41a0*);
struct Statica41a0 {
    void* value;
    Statica41a0() { construct(this, &descriptor); }
    ~Statica41a0() { destroy(this); }
};
