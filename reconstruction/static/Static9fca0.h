// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fca0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fca0;
extern void construct(Static9fca0*, const Descriptor*);
extern void destroy(Static9fca0*);
struct Static9fca0 {
    void* value;
    Static9fca0() { construct(this, &descriptor); }
    ~Static9fca0() { destroy(this); }
};
