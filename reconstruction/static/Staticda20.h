// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticda20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticda20;
extern void construct(Staticda20*, const Descriptor*);
extern void destroy(Staticda20*);
struct Staticda20 {
    void* value;
    Staticda20() { construct(this, &descriptor); }
    ~Staticda20() { destroy(this); }
};
