// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103070, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103070;
extern void construct(Static103070*, const Descriptor*);
extern void destroy(Static103070*);
struct Static103070 {
    void* value;
    Static103070() { construct(this, &descriptor); }
    ~Static103070() { destroy(this); }
};
