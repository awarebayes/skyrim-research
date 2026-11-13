// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97cf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97cf0;
extern void construct(Static97cf0*, const Descriptor*);
extern void destroy(Static97cf0*);
struct Static97cf0 {
    void* value;
    Static97cf0() { construct(this, &descriptor); }
    ~Static97cf0() { destroy(this); }
};
