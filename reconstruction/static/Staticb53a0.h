// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb53a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb53a0;
extern void construct(Staticb53a0*, const Descriptor*);
extern void destroy(Staticb53a0*);
struct Staticb53a0 {
    void* value;
    Staticb53a0() { construct(this, &descriptor); }
    ~Staticb53a0() { destroy(this); }
};
