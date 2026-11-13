// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6ad0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6ad0;
extern void construct(Statica6ad0*, const Descriptor*);
extern void destroy(Statica6ad0*);
struct Statica6ad0 {
    void* value;
    Statica6ad0() { construct(this, &descriptor); }
    ~Statica6ad0() { destroy(this); }
};
