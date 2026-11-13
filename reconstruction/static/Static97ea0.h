// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97ea0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97ea0;
extern void construct(Static97ea0*, const Descriptor*);
extern void destroy(Static97ea0*);
struct Static97ea0 {
    void* value;
    Static97ea0() { construct(this, &descriptor); }
    ~Static97ea0() { destroy(this); }
};
