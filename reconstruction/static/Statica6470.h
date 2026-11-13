// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6470, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6470;
extern void construct(Statica6470*, const Descriptor*);
extern void destroy(Statica6470*);
struct Statica6470 {
    void* value;
    Statica6470() { construct(this, &descriptor); }
    ~Statica6470() { destroy(this); }
};
