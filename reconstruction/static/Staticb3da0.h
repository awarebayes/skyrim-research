// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3da0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3da0;
extern void construct(Staticb3da0*, const Descriptor*);
extern void destroy(Staticb3da0*);
struct Staticb3da0 {
    void* value;
    Staticb3da0() { construct(this, &descriptor); }
    ~Staticb3da0() { destroy(this); }
};
