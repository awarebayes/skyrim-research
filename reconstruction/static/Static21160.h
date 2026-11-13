// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21160, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21160;
extern void construct(Static21160*, const Descriptor*);
extern void destroy(Static21160*);
struct Static21160 {
    void* value;
    Static21160() { construct(this, &descriptor); }
    ~Static21160() { destroy(this); }
};
