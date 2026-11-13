// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb74e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb74e0;
extern void construct(Staticb74e0*, const Descriptor*);
extern void destroy(Staticb74e0*);
struct Staticb74e0 {
    void* value;
    Staticb74e0() { construct(this, &descriptor); }
    ~Staticb74e0() { destroy(this); }
};
