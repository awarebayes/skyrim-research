// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static210d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static210d0;
extern void construct(Static210d0*, const Descriptor*);
extern void destroy(Static210d0*);
struct Static210d0 {
    void* value;
    Static210d0() { construct(this, &descriptor); }
    ~Static210d0() { destroy(this); }
};
