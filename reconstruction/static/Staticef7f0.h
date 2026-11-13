// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef7f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef7f0;
extern void construct(Staticef7f0*, const Descriptor*);
extern void destroy(Staticef7f0*);
struct Staticef7f0 {
    void* value;
    Staticef7f0() { construct(this, &descriptor); }
    ~Staticef7f0() { destroy(this); }
};
