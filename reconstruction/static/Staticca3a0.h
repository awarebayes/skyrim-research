// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca3a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca3a0;
extern void construct(Staticca3a0*, const Descriptor*);
extern void destroy(Staticca3a0*);
struct Staticca3a0 {
    void* value;
    Staticca3a0() { construct(this, &descriptor); }
    ~Staticca3a0() { destroy(this); }
};
