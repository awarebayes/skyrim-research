// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf2ea0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf2ea0;
extern void construct(Staticf2ea0*, const Descriptor*);
extern void destroy(Staticf2ea0*);
struct Staticf2ea0 {
    void* value;
    Staticf2ea0() { construct(this, &descriptor); }
    ~Staticf2ea0() { destroy(this); }
};
