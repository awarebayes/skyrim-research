// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9e9c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9e9c0;
extern void construct(Static9e9c0*, const Descriptor*);
extern void destroy(Static9e9c0*);
struct Static9e9c0 {
    void* value;
    Static9e9c0() { construct(this, &descriptor); }
    ~Static9e9c0() { destroy(this); }
};
