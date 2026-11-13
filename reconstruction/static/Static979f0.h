// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static979f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static979f0;
extern void construct(Static979f0*, const Descriptor*);
extern void destroy(Static979f0*);
struct Static979f0 {
    void* value;
    Static979f0() { construct(this, &descriptor); }
    ~Static979f0() { destroy(this); }
};
