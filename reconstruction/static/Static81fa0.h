// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static81fa0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static81fa0;
extern void construct(Static81fa0*, const Descriptor*);
extern void destroy(Static81fa0*);
struct Static81fa0 {
    void* value;
    Static81fa0() { construct(this, &descriptor); }
    ~Static81fa0() { destroy(this); }
};
