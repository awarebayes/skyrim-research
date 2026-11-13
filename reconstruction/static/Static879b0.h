// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static879b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static879b0;
extern void construct(Static879b0*, const Descriptor*);
extern void destroy(Static879b0*);
struct Static879b0 {
    void* value;
    Static879b0() { construct(this, &descriptor); }
    ~Static879b0() { destroy(this); }
};
