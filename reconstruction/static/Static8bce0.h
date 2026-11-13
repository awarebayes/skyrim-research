// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8bce0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8bce0;
extern void construct(Static8bce0*, const Descriptor*);
extern void destroy(Static8bce0*);
struct Static8bce0 {
    void* value;
    Static8bce0() { construct(this, &descriptor); }
    ~Static8bce0() { destroy(this); }
};
