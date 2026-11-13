// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15be0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15be0;
extern void construct(Static15be0*, const Descriptor*);
extern void destroy(Static15be0*);
struct Static15be0 {
    void* value;
    Static15be0() { construct(this, &descriptor); }
    ~Static15be0() { destroy(this); }
};
