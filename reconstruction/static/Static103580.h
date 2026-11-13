// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103580, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103580;
extern void construct(Static103580*, const Descriptor*);
extern void destroy(Static103580*);
struct Static103580 {
    void* value;
    Static103580() { construct(this, &descriptor); }
    ~Static103580() { destroy(this); }
};
