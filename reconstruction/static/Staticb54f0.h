// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb54f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb54f0;
extern void construct(Staticb54f0*, const Descriptor*);
extern void destroy(Staticb54f0*);
struct Staticb54f0 {
    void* value;
    Staticb54f0() { construct(this, &descriptor); }
    ~Staticb54f0() { destroy(this); }
};
