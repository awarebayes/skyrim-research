// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15cd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15cd0;
extern void construct(Static15cd0*, const Descriptor*);
extern void destroy(Static15cd0*);
struct Static15cd0 {
    void* value;
    Static15cd0() { construct(this, &descriptor); }
    ~Static15cd0() { destroy(this); }
};
