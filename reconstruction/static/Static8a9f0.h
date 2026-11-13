// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8a9f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8a9f0;
extern void construct(Static8a9f0*, const Descriptor*);
extern void destroy(Static8a9f0*);
struct Static8a9f0 {
    void* value;
    Static8a9f0() { construct(this, &descriptor); }
    ~Static8a9f0() { destroy(this); }
};
