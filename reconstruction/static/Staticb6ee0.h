// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6ee0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6ee0;
extern void construct(Staticb6ee0*, const Descriptor*);
extern void destroy(Staticb6ee0*);
struct Staticb6ee0 {
    void* value;
    Staticb6ee0() { construct(this, &descriptor); }
    ~Staticb6ee0() { destroy(this); }
};
