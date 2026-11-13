// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb67a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb67a0;
extern void construct(Staticb67a0*, const Descriptor*);
extern void destroy(Staticb67a0*);
struct Staticb67a0 {
    void* value;
    Staticb67a0() { construct(this, &descriptor); }
    ~Staticb67a0() { destroy(this); }
};
