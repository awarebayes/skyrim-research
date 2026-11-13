// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8b060, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8b060;
extern void construct(Static8b060*, const Descriptor*);
extern void destroy(Static8b060*);
struct Static8b060 {
    void* value;
    Static8b060() { construct(this, &descriptor); }
    ~Static8b060() { destroy(this); }
};
