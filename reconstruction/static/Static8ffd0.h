// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8ffd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8ffd0;
extern void construct(Static8ffd0*, const Descriptor*);
extern void destroy(Static8ffd0*);
struct Static8ffd0 {
    void* value;
    Static8ffd0() { construct(this, &descriptor); }
    ~Static8ffd0() { destroy(this); }
};
