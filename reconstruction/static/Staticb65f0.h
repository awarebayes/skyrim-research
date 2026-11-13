// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb65f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb65f0;
extern void construct(Staticb65f0*, const Descriptor*);
extern void destroy(Staticb65f0*);
struct Staticb65f0 {
    void* value;
    Staticb65f0() { construct(this, &descriptor); }
    ~Staticb65f0() { destroy(this); }
};
