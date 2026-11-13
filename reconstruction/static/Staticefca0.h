// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefca0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefca0;
extern void construct(Staticefca0*, const Descriptor*);
extern void destroy(Staticefca0*);
struct Staticefca0 {
    void* value;
    Staticefca0() { construct(this, &descriptor); }
    ~Staticefca0() { destroy(this); }
};
