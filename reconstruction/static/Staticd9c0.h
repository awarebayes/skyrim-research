// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd9c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd9c0;
extern void construct(Staticd9c0*, const Descriptor*);
extern void destroy(Staticd9c0*);
struct Staticd9c0 {
    void* value;
    Staticd9c0() { construct(this, &descriptor); }
    ~Staticd9c0() { destroy(this); }
};
