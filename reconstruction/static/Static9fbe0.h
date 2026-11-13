// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fbe0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fbe0;
extern void construct(Static9fbe0*, const Descriptor*);
extern void destroy(Static9fbe0*);
struct Static9fbe0 {
    void* value;
    Static9fbe0() { construct(this, &descriptor); }
    ~Static9fbe0() { destroy(this); }
};
