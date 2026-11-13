// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fd60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fd60;
extern void construct(Static8fd60*, const Descriptor*);
extern void destroy(Static8fd60*);
struct Static8fd60 {
    void* value;
    Static8fd60() { construct(this, &descriptor); }
    ~Static8fd60() { destroy(this); }
};
