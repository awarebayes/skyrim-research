// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb78e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb78e0;
extern void construct(Staticb78e0*, const Descriptor*);
extern void destroy(Staticb78e0*);
struct Staticb78e0 {
    void* value;
    Staticb78e0() { construct(this, &descriptor); }
    ~Staticb78e0() { destroy(this); }
};
