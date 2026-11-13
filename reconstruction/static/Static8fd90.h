// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fd90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fd90;
extern void construct(Static8fd90*, const Descriptor*);
extern void destroy(Static8fd90*);
struct Static8fd90 {
    void* value;
    Static8fd90() { construct(this, &descriptor); }
    ~Static8fd90() { destroy(this); }
};
