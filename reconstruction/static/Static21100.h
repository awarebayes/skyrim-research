// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21100, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21100;
extern void construct(Static21100*, const Descriptor*);
extern void destroy(Static21100*);
struct Static21100 {
    void* value;
    Static21100() { construct(this, &descriptor); }
    ~Static21100() { destroy(this); }
};
