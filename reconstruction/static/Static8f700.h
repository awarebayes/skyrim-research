// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8f700, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8f700;
extern void construct(Static8f700*, const Descriptor*);
extern void destroy(Static8f700*);
struct Static8f700 {
    void* value;
    Static8f700() { construct(this, &descriptor); }
    ~Static8f700() { destroy(this); }
};
