// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15e20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15e20;
extern void construct(Static15e20*, const Descriptor*);
extern void destroy(Static15e20*);
struct Static15e20 {
    void* value;
    Static15e20() { construct(this, &descriptor); }
    ~Static15e20() { destroy(this); }
};
