// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticfbd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticfbd0;
extern void construct(Staticfbd0*, const Descriptor*);
extern void destroy(Staticfbd0*);
struct Staticfbd0 {
    void* value;
    Staticfbd0() { construct(this, &descriptor); }
    ~Staticfbd0() { destroy(this); }
};
