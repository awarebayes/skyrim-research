// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd3c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd3c0;
extern void construct(Staticd3c0*, const Descriptor*);
extern void destroy(Staticd3c0*);
struct Staticd3c0 {
    void* value;
    Staticd3c0() { construct(this, &descriptor); }
    ~Staticd3c0() { destroy(this); }
};
