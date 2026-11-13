// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static900c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static900c0;
extern void construct(Static900c0*, const Descriptor*);
extern void destroy(Static900c0*);
struct Static900c0 {
    void* value;
    Static900c0() { construct(this, &descriptor); }
    ~Static900c0() { destroy(this); }
};
