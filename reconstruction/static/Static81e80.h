// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static81e80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static81e80;
extern void construct(Static81e80*, const Descriptor*);
extern void destroy(Static81e80*);
struct Static81e80 {
    void* value;
    Static81e80() { construct(this, &descriptor); }
    ~Static81e80() { destroy(this); }
};
