// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static883b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static883b0;
extern void construct(Static883b0*, const Descriptor*);
extern void destroy(Static883b0*);
struct Static883b0 {
    void* value;
    Static883b0() { construct(this, &descriptor); }
    ~Static883b0() { destroy(this); }
};
