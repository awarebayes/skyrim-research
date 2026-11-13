// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fc10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fc10;
extern void construct(Static8fc10*, const Descriptor*);
extern void destroy(Static8fc10*);
struct Static8fc10 {
    void* value;
    Static8fc10() { construct(this, &descriptor); }
    ~Static8fc10() { destroy(this); }
};
