// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fbb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fbb0;
extern void construct(Static9fbb0*, const Descriptor*);
extern void destroy(Static9fbb0*);
struct Static9fbb0 {
    void* value;
    Static9fbb0() { construct(this, &descriptor); }
    ~Static9fbb0() { destroy(this); }
};
