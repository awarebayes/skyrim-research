// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd0f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd0f0;
extern void construct(Staticd0f0*, const Descriptor*);
extern void destroy(Staticd0f0*);
struct Staticd0f0 {
    void* value;
    Staticd0f0() { construct(this, &descriptor); }
    ~Staticd0f0() { destroy(this); }
};
