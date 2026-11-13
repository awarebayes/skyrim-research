// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8b7e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8b7e0;
extern void construct(Static8b7e0*, const Descriptor*);
extern void destroy(Static8b7e0*);
struct Static8b7e0 {
    void* value;
    Static8b7e0() { construct(this, &descriptor); }
    ~Static8b7e0() { destroy(this); }
};
