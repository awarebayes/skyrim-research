// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8fc40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8fc40;
extern void construct(Static8fc40*, const Descriptor*);
extern void destroy(Static8fc40*);
struct Static8fc40 {
    void* value;
    Static8fc40() { construct(this, &descriptor); }
    ~Static8fc40() { destroy(this); }
};
