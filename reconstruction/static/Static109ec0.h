// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109ec0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109ec0;
extern void construct(Static109ec0*, const Descriptor*);
extern void destroy(Static109ec0*);
struct Static109ec0 {
    void* value;
    Static109ec0() { construct(this, &descriptor); }
    ~Static109ec0() { destroy(this); }
};
