// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15ca0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15ca0;
extern void construct(Static15ca0*, const Descriptor*);
extern void destroy(Static15ca0*);
struct Static15ca0 {
    void* value;
    Static15ca0() { construct(this, &descriptor); }
    ~Static15ca0() { destroy(this); }
};
