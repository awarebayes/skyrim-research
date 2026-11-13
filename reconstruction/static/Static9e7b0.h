// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9e7b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9e7b0;
extern void construct(Static9e7b0*, const Descriptor*);
extern void destroy(Static9e7b0*);
struct Static9e7b0 {
    void* value;
    Static9e7b0() { construct(this, &descriptor); }
    ~Static9e7b0() { destroy(this); }
};
