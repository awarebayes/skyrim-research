// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103220, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103220;
extern void construct(Static103220*, const Descriptor*);
extern void destroy(Static103220*);
struct Static103220 {
    void* value;
    Static103220() { construct(this, &descriptor); }
    ~Static103220() { destroy(this); }
};
