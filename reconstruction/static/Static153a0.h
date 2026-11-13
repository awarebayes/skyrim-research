// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static153a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static153a0;
extern void construct(Static153a0*, const Descriptor*);
extern void destroy(Static153a0*);
struct Static153a0 {
    void* value;
    Static153a0() { construct(this, &descriptor); }
    ~Static153a0() { destroy(this); }
};
