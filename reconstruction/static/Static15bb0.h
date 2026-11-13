// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15bb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15bb0;
extern void construct(Static15bb0*, const Descriptor*);
extern void destroy(Static15bb0*);
struct Static15bb0 {
    void* value;
    Static15bb0() { construct(this, &descriptor); }
    ~Static15bb0() { destroy(this); }
};
