// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8ab90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8ab90;
extern void construct(Static8ab90*, const Descriptor*);
extern void destroy(Static8ab90*);
struct Static8ab90 {
    void* value;
    Static8ab90() { construct(this, &descriptor); }
    ~Static8ab90() { destroy(this); }
};
