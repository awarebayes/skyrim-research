// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fc70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fc70;
extern void construct(Static8fc70*, const Descriptor*);
extern void destroy(Static8fc70*);
struct Static8fc70 {
    void* value;
    Static8fc70() { construct(this, &descriptor); }
    ~Static8fc70() { destroy(this); }
};
