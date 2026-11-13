// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static213d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static213d0;
extern void construct(Static213d0*, const Descriptor*);
extern void destroy(Static213d0*);
struct Static213d0 {
    void* value;
    Static213d0() { construct(this, &descriptor); }
    ~Static213d0() { destroy(this); }
};
