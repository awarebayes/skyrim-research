// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8b390, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8b390;
extern void construct(Static8b390*, const Descriptor*);
extern void destroy(Static8b390*);
struct Static8b390 {
    void* value;
    Static8b390() { construct(this, &descriptor); }
    ~Static8b390() { destroy(this); }
};
