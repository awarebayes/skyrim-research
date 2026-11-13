// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef4f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef4f0;
extern void construct(Staticef4f0*, const Descriptor*);
extern void destroy(Staticef4f0*);
struct Staticef4f0 {
    void* value;
    Staticef4f0() { construct(this, &descriptor); }
    ~Staticef4f0() { destroy(this); }
};
