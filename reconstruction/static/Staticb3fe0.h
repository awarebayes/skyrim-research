// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3fe0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3fe0;
extern void construct(Staticb3fe0*, const Descriptor*);
extern void destroy(Staticb3fe0*);
struct Staticb3fe0 {
    void* value;
    Staticb3fe0() { construct(this, &descriptor); }
    ~Staticb3fe0() { destroy(this); }
};
