// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8420, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8420;
extern void construct(Static8420*, const Descriptor*);
extern void destroy(Static8420*);
struct Static8420 {
    void* value;
    Static8420() { construct(this, &descriptor); }
    ~Static8420() { destroy(this); }
};
