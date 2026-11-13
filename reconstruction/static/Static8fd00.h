// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fd00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fd00;
extern void construct(Static8fd00*, const Descriptor*);
extern void destroy(Static8fd00*);
struct Static8fd00 {
    void* value;
    Static8fd00() { construct(this, &descriptor); }
    ~Static8fd00() { destroy(this); }
};
