// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd1e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd1e0;
extern void construct(Staticd1e0*, const Descriptor*);
extern void destroy(Staticd1e0*);
struct Staticd1e0 {
    void* value;
    Staticd1e0() { construct(this, &descriptor); }
    ~Staticd1e0() { destroy(this); }
};
