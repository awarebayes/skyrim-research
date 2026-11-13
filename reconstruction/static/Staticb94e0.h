// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb94e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb94e0;
extern void construct(Staticb94e0*, const Descriptor*);
extern void destroy(Staticb94e0*);
struct Staticb94e0 {
    void* value;
    Staticb94e0() { construct(this, &descriptor); }
    ~Staticb94e0() { destroy(this); }
};
