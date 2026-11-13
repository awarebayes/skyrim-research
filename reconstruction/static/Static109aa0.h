// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109aa0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109aa0;
extern void construct(Static109aa0*, const Descriptor*);
extern void destroy(Static109aa0*);
struct Static109aa0 {
    void* value;
    Static109aa0() { construct(this, &descriptor); }
    ~Static109aa0() { destroy(this); }
};
