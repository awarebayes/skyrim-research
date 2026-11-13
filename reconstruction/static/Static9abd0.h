// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9abd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9abd0;
extern void construct(Static9abd0*, const Descriptor*);
extern void destroy(Static9abd0*);
struct Static9abd0 {
    void* value;
    Static9abd0() { construct(this, &descriptor); }
    ~Static9abd0() { destroy(this); }
};
