// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21310, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21310;
extern void construct(Static21310*, const Descriptor*);
extern void destroy(Static21310*);
struct Static21310 {
    void* value;
    Static21310() { construct(this, &descriptor); }
    ~Static21310() { destroy(this); }
};
