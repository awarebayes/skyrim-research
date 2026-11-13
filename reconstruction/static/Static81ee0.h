// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static81ee0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static81ee0;
extern void construct(Static81ee0*, const Descriptor*);
extern void destroy(Static81ee0*);
struct Static81ee0 {
    void* value;
    Static81ee0() { construct(this, &descriptor); }
    ~Static81ee0() { destroy(this); }
};
