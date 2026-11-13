// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8f9a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8f9a0;
extern void construct(Static8f9a0*, const Descriptor*);
extern void destroy(Static8f9a0*);
struct Static8f9a0 {
    void* value;
    Static8f9a0() { construct(this, &descriptor); }
    ~Static8f9a0() { destroy(this); }
};
