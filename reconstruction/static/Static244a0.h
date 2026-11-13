// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static244a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static244a0;
extern void construct(Static244a0*, const Descriptor*);
extern void destroy(Static244a0*);
struct Static244a0 {
    void* value;
    Static244a0() { construct(this, &descriptor); }
    ~Static244a0() { destroy(this); }
};
