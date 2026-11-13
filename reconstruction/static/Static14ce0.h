// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static14ce0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static14ce0;
extern void construct(Static14ce0*, const Descriptor*);
extern void destroy(Static14ce0*);
struct Static14ce0 {
    void* value;
    Static14ce0() { construct(this, &descriptor); }
    ~Static14ce0() { destroy(this); }
};
