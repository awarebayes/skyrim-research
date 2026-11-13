// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static876e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static876e0;
extern void construct(Static876e0*, const Descriptor*);
extern void destroy(Static876e0*);
struct Static876e0 {
    void* value;
    Static876e0() { construct(this, &descriptor); }
    ~Static876e0() { destroy(this); }
};
