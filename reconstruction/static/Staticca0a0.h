// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca0a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca0a0;
extern void construct(Staticca0a0*, const Descriptor*);
extern void destroy(Staticca0a0*);
struct Staticca0a0 {
    void* value;
    Staticca0a0() { construct(this, &descriptor); }
    ~Staticca0a0() { destroy(this); }
};
