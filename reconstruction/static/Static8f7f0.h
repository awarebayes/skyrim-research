// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8f7f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8f7f0;
extern void construct(Static8f7f0*, const Descriptor*);
extern void destroy(Static8f7f0*);
struct Static8f7f0 {
    void* value;
    Static8f7f0() { construct(this, &descriptor); }
    ~Static8f7f0() { destroy(this); }
};
