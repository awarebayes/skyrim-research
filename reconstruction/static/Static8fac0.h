// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fac0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fac0;
extern void construct(Static8fac0*, const Descriptor*);
extern void destroy(Static8fac0*);
struct Static8fac0 {
    void* value;
    Static8fac0() { construct(this, &descriptor); }
    ~Static8fac0() { destroy(this); }
};
