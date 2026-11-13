// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103160, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103160;
extern void construct(Static103160*, const Descriptor*);
extern void destroy(Static103160*);
struct Static103160 {
    void* value;
    Static103160() { construct(this, &descriptor); }
    ~Static103160() { destroy(this); }
};
