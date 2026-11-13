// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb95a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb95a0;
extern void construct(Staticb95a0*, const Descriptor*);
extern void destroy(Staticb95a0*);
struct Staticb95a0 {
    void* value;
    Staticb95a0() { construct(this, &descriptor); }
    ~Staticb95a0() { destroy(this); }
};
