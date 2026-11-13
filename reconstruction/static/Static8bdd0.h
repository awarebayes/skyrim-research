// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8bdd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8bdd0;
extern void construct(Static8bdd0*, const Descriptor*);
extern void destroy(Static8bdd0*);
struct Static8bdd0 {
    void* value;
    Static8bdd0() { construct(this, &descriptor); }
    ~Static8bdd0() { destroy(this); }
};
