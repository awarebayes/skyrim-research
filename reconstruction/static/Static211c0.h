// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static211c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static211c0;
extern void construct(Static211c0*, const Descriptor*);
extern void destroy(Static211c0*);
struct Static211c0 {
    void* value;
    Static211c0() { construct(this, &descriptor); }
    ~Static211c0() { destroy(this); }
};
