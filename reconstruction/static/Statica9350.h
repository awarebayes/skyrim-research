// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica9350, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica9350;
extern void construct(Statica9350*, const Descriptor*);
extern void destroy(Statica9350*);
struct Statica9350 {
    void* value;
    Statica9350() { construct(this, &descriptor); }
    ~Statica9350() { destroy(this); }
};
