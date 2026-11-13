// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static17ce0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static17ce0;
extern void construct(Static17ce0*, const Descriptor*);
extern void destroy(Static17ce0*);
struct Static17ce0 {
    void* value;
    Static17ce0() { construct(this, &descriptor); }
    ~Static17ce0() { destroy(this); }
};
