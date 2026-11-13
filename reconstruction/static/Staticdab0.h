// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticdab0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticdab0;
extern void construct(Staticdab0*, const Descriptor*);
extern void destroy(Staticdab0*);
struct Staticdab0 {
    void* value;
    Staticdab0() { construct(this, &descriptor); }
    ~Staticdab0() { destroy(this); }
};
