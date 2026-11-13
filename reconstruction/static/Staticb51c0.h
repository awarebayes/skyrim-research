// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb51c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb51c0;
extern void construct(Staticb51c0*, const Descriptor*);
extern void destroy(Staticb51c0*);
struct Staticb51c0 {
    void* value;
    Staticb51c0() { construct(this, &descriptor); }
    ~Staticb51c0() { destroy(this); }
};
