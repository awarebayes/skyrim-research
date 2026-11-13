// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca0d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca0d0;
extern void construct(Staticca0d0*, const Descriptor*);
extern void destroy(Staticca0d0*);
struct Staticca0d0 {
    void* value;
    Staticca0d0() { construct(this, &descriptor); }
    ~Staticca0d0() { destroy(this); }
};
