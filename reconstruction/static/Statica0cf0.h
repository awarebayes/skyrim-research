// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0cf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0cf0;
extern void construct(Statica0cf0*, const Descriptor*);
extern void destroy(Statica0cf0*);
struct Statica0cf0 {
    void* value;
    Statica0cf0() { construct(this, &descriptor); }
    ~Statica0cf0() { destroy(this); }
};
