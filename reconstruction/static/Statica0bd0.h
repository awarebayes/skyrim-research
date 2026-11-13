// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0bd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0bd0;
extern void construct(Statica0bd0*, const Descriptor*);
extern void destroy(Statica0bd0*);
struct Statica0bd0 {
    void* value;
    Statica0bd0() { construct(this, &descriptor); }
    ~Statica0bd0() { destroy(this); }
};
