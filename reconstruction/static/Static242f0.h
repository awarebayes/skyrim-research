// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static242f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static242f0;
extern void construct(Static242f0*, const Descriptor*);
extern void destroy(Static242f0*);
struct Static242f0 {
    void* value;
    Static242f0() { construct(this, &descriptor); }
    ~Static242f0() { destroy(this); }
};
