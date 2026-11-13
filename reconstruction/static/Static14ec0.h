// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static14ec0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static14ec0;
extern void construct(Static14ec0*, const Descriptor*);
extern void destroy(Static14ec0*);
struct Static14ec0 {
    void* value;
    Static14ec0() { construct(this, &descriptor); }
    ~Static14ec0() { destroy(this); }
};
