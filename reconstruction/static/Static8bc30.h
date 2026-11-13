// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8bc30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8bc30;
extern void construct(Static8bc30*, const Descriptor*);
extern void destroy(Static8bc30*);
struct Static8bc30 {
    void* value;
    Static8bc30() { construct(this, &descriptor); }
    ~Static8bc30() { destroy(this); }
};
