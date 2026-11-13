// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6da0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6da0;
extern void construct(Statica6da0*, const Descriptor*);
extern void destroy(Statica6da0*);
struct Statica6da0 {
    void* value;
    Statica6da0() { construct(this, &descriptor); }
    ~Statica6da0() { destroy(this); }
};
