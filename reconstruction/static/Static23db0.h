// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23db0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23db0;
extern void construct(Static23db0*, const Descriptor*);
extern void destroy(Static23db0*);
struct Static23db0 {
    void* value;
    Static23db0() { construct(this, &descriptor); }
    ~Static23db0() { destroy(this); }
};
