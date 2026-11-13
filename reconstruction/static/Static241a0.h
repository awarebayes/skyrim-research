// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static241a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static241a0;
extern void construct(Static241a0*, const Descriptor*);
extern void destroy(Static241a0*);
struct Static241a0 {
    void* value;
    Static241a0() { construct(this, &descriptor); }
    ~Static241a0() { destroy(this); }
};
