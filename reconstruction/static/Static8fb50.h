// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fb50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fb50;
extern void construct(Static8fb50*, const Descriptor*);
extern void destroy(Static8fb50*);
struct Static8fb50 {
    void* value;
    Static8fb50() { construct(this, &descriptor); }
    ~Static8fb50() { destroy(this); }
};
