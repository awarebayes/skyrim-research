// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static8af40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static8af40;
extern void construct(Static8af40*, const Descriptor*);
extern void destroy(Static8af40*);
struct Static8af40 {
    void* value;
    Static8af40() { construct(this, &descriptor); }
    ~Static8af40() { destroy(this); }
};
