// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7de0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7de0;
extern void construct(Staticb7de0*, const Descriptor*);
extern void destroy(Staticb7de0*);
struct Staticb7de0 {
    void* value;
    Staticb7de0() { construct(this, &descriptor); }
    ~Staticb7de0() { destroy(this); }
};
