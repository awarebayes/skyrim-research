// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefac0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefac0;
extern void construct(Staticefac0*, const Descriptor*);
extern void destroy(Staticefac0*);
struct Staticefac0 {
    void* value;
    Staticefac0() { construct(this, &descriptor); }
    ~Staticefac0() { destroy(this); }
};
