// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefcd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefcd0;
extern void construct(Staticefcd0*, const Descriptor*);
extern void destroy(Staticefcd0*);
struct Staticefcd0 {
    void* value;
    Staticefcd0() { construct(this, &descriptor); }
    ~Staticefcd0() { destroy(this); }
};
