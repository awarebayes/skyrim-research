// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0db0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0db0;
extern void construct(Statica0db0*, const Descriptor*);
extern void destroy(Statica0db0*);
struct Statica0db0 {
    void* value;
    Statica0db0() { construct(this, &descriptor); }
    ~Statica0db0() { destroy(this); }
};
