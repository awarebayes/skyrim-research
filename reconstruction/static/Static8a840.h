// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8a840, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8a840;
extern void construct(Static8a840*, const Descriptor*);
extern void destroy(Static8a840*);
struct Static8a840 {
    void* value;
    Static8a840() { construct(this, &descriptor); }
    ~Static8a840() { destroy(this); }
};
