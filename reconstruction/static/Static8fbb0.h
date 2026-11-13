// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fbb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fbb0;
extern void construct(Static8fbb0*, const Descriptor*);
extern void destroy(Static8fbb0*);
struct Static8fbb0 {
    void* value;
    Static8fbb0() { construct(this, &descriptor); }
    ~Static8fbb0() { destroy(this); }
};
