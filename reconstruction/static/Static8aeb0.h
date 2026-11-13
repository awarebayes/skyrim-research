// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8aeb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8aeb0;
extern void construct(Static8aeb0*, const Descriptor*);
extern void destroy(Static8aeb0*);
struct Static8aeb0 {
    void* value;
    Static8aeb0() { construct(this, &descriptor); }
    ~Static8aeb0() { destroy(this); }
};
