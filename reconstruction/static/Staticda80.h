// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticda80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticda80;
extern void construct(Staticda80*, const Descriptor*);
extern void destroy(Staticda80*);
struct Staticda80 {
    void* value;
    Staticda80() { construct(this, &descriptor); }
    ~Staticda80() { destroy(this); }
};
