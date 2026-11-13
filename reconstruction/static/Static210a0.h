// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static210a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static210a0;
extern void construct(Static210a0*, const Descriptor*);
extern void destroy(Static210a0*);
struct Static210a0 {
    void* value;
    Static210a0() { construct(this, &descriptor); }
    ~Static210a0() { destroy(this); }
};
