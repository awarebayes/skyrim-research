// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef8e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef8e0;
extern void construct(Staticef8e0*, const Descriptor*);
extern void destroy(Staticef8e0*);
struct Staticef8e0 {
    void* value;
    Staticef8e0() { construct(this, &descriptor); }
    ~Staticef8e0() { destroy(this); }
};
