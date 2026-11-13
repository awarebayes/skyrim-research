// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8ae20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8ae20;
extern void construct(Static8ae20*, const Descriptor*);
extern void destroy(Static8ae20*);
struct Static8ae20 {
    void* value;
    Static8ae20() { construct(this, &descriptor); }
    ~Static8ae20() { destroy(this); }
};
