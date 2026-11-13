// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static91600, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static91600;
extern void construct(Static91600*, const Descriptor*);
extern void destroy(Static91600*);
struct Static91600 {
    void* value;
    Static91600() { construct(this, &descriptor); }
    ~Static91600() { destroy(this); }
};
