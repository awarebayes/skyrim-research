// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8c0c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8c0c0;
extern void construct(Static8c0c0*, const Descriptor*);
extern void destroy(Static8c0c0*);
struct Static8c0c0 {
    void* value;
    Static8c0c0() { construct(this, &descriptor); }
    ~Static8c0c0() { destroy(this); }
};
