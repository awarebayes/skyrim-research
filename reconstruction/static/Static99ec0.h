// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static99ec0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static99ec0;
extern void construct(Static99ec0*, const Descriptor*);
extern void destroy(Static99ec0*);
struct Static99ec0 {
    void* value;
    Static99ec0() { construct(this, &descriptor); }
    ~Static99ec0() { destroy(this); }
};
