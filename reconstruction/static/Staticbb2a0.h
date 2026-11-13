// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb2a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb2a0;
extern void construct(Staticbb2a0*, const Descriptor*);
extern void destroy(Staticbb2a0*);
struct Staticbb2a0 {
    void* value;
    Staticbb2a0() { construct(this, &descriptor); }
    ~Staticbb2a0() { destroy(this); }
};
