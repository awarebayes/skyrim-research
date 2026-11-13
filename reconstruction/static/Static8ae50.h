// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8ae50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8ae50;
extern void construct(Static8ae50*, const Descriptor*);
extern void destroy(Static8ae50*);
struct Static8ae50 {
    void* value;
    Static8ae50() { construct(this, &descriptor); }
    ~Static8ae50() { destroy(this); }
};
