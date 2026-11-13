// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fe80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fe80;
extern void construct(Static8fe80*, const Descriptor*);
extern void destroy(Static8fe80*);
struct Static8fe80 {
    void* value;
    Static8fe80() { construct(this, &descriptor); }
    ~Static8fe80() { destroy(this); }
};
