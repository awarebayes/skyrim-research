// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb73c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb73c0;
extern void construct(Staticb73c0*, const Descriptor*);
extern void destroy(Staticb73c0*);
struct Staticb73c0 {
    void* value;
    Staticb73c0() { construct(this, &descriptor); }
    ~Staticb73c0() { destroy(this); }
};
