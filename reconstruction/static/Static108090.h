// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108090, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108090;
extern void construct(Static108090*, const Descriptor*);
extern void destroy(Static108090*);
struct Static108090 {
    void* value;
    Static108090() { construct(this, &descriptor); }
    ~Static108090() { destroy(this); }
};
