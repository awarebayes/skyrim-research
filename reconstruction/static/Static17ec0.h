// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static17ec0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static17ec0;
extern void construct(Static17ec0*, const Descriptor*);
extern void destroy(Static17ec0*);
struct Static17ec0 {
    void* value;
    Static17ec0() { construct(this, &descriptor); }
    ~Static17ec0() { destroy(this); }
};
