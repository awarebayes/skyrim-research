// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21af0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21af0;
extern void construct(Static21af0*, const Descriptor*);
extern void destroy(Static21af0*);
struct Static21af0 {
    void* value;
    Static21af0() { construct(this, &descriptor); }
    ~Static21af0() { destroy(this); }
};
