// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6eb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6eb0;
extern void construct(Staticb6eb0*, const Descriptor*);
extern void destroy(Staticb6eb0*);
struct Staticb6eb0 {
    void* value;
    Staticb6eb0() { construct(this, &descriptor); }
    ~Staticb6eb0() { destroy(this); }
};
