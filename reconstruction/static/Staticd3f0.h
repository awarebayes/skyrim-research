// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd3f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd3f0;
extern void construct(Staticd3f0*, const Descriptor*);
extern void destroy(Staticd3f0*);
struct Staticd3f0 {
    void* value;
    Staticd3f0() { construct(this, &descriptor); }
    ~Staticd3f0() { destroy(this); }
};
