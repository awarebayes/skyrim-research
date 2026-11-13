// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb55e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb55e0;
extern void construct(Staticb55e0*, const Descriptor*);
extern void destroy(Staticb55e0*);
struct Staticb55e0 {
    void* value;
    Staticb55e0() { construct(this, &descriptor); }
    ~Staticb55e0() { destroy(this); }
};
