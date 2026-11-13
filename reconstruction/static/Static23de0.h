// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23de0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23de0;
extern void construct(Static23de0*, const Descriptor*);
extern void destroy(Static23de0*);
struct Static23de0 {
    void* value;
    Static23de0() { construct(this, &descriptor); }
    ~Static23de0() { destroy(this); }
};
