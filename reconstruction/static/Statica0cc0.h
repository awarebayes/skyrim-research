// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0cc0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0cc0;
extern void construct(Statica0cc0*, const Descriptor*);
extern void destroy(Statica0cc0*);
struct Statica0cc0 {
    void* value;
    Statica0cc0() { construct(this, &descriptor); }
    ~Statica0cc0() { destroy(this); }
};
