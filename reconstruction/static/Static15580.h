// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15580, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15580;
extern void construct(Static15580*, const Descriptor*);
extern void destroy(Static15580*);
struct Static15580 {
    void* value;
    Static15580() { construct(this, &descriptor); }
    ~Static15580() { destroy(this); }
};
