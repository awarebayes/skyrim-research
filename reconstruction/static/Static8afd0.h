// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8afd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8afd0;
extern void construct(Static8afd0*, const Descriptor*);
extern void destroy(Static8afd0*);
struct Static8afd0 {
    void* value;
    Static8afd0() { construct(this, &descriptor); }
    ~Static8afd0() { destroy(this); }
};
