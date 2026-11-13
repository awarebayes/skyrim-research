// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb72d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb72d0;
extern void construct(Staticb72d0*, const Descriptor*);
extern void destroy(Staticb72d0*);
struct Staticb72d0 {
    void* value;
    Staticb72d0() { construct(this, &descriptor); }
    ~Staticb72d0() { destroy(this); }
};
