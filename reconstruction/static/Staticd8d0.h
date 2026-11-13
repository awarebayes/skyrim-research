// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd8d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd8d0;
extern void construct(Staticd8d0*, const Descriptor*);
extern void destroy(Staticd8d0*);
struct Staticd8d0 {
    void* value;
    Staticd8d0() { construct(this, &descriptor); }
    ~Staticd8d0() { destroy(this); }
};
