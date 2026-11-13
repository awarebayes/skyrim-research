// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf5db0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf5db0;
extern void construct(Staticf5db0*, const Descriptor*);
extern void destroy(Staticf5db0*);
struct Staticf5db0 {
    void* value;
    Staticf5db0() { construct(this, &descriptor); }
    ~Staticf5db0() { destroy(this); }
};
