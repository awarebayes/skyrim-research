// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9efc0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9efc0;
extern void construct(Static9efc0*, const Descriptor*);
extern void destroy(Static9efc0*);
struct Static9efc0 {
    void* value;
    Static9efc0() { construct(this, &descriptor); }
    ~Static9efc0() { destroy(this); }
};
