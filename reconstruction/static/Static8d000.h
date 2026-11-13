// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8d000, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8d000;
extern void construct(Static8d000*, const Descriptor*);
extern void destroy(Static8d000*);
struct Static8d000 {
    void* value;
    Static8d000() { construct(this, &descriptor); }
    ~Static8d000() { destroy(this); }
};
