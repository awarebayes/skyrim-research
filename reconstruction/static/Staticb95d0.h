// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb95d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb95d0;
extern void construct(Staticb95d0*, const Descriptor*);
extern void destroy(Staticb95d0*);
struct Staticb95d0 {
    void* value;
    Staticb95d0() { construct(this, &descriptor); }
    ~Staticb95d0() { destroy(this); }
};
