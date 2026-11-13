// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fcd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fcd0;
extern void construct(Static8fcd0*, const Descriptor*);
extern void destroy(Static8fcd0*);
struct Static8fcd0 {
    void* value;
    Static8fcd0() { construct(this, &descriptor); }
    ~Static8fcd0() { destroy(this); }
};
