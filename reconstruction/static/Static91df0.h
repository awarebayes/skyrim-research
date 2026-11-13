// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static91df0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static91df0;
extern void construct(Static91df0*, const Descriptor*);
extern void destroy(Static91df0*);
struct Static91df0 {
    void* value;
    Static91df0() { construct(this, &descriptor); }
    ~Static91df0() { destroy(this); }
};
