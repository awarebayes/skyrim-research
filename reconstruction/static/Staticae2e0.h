// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticae2e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticae2e0;
extern void construct(Staticae2e0*, const Descriptor*);
extern void destroy(Staticae2e0*);
struct Staticae2e0 {
    void* value;
    Staticae2e0() { construct(this, &descriptor); }
    ~Staticae2e0() { destroy(this); }
};
