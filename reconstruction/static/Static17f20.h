// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static17f20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static17f20;
extern void construct(Static17f20*, const Descriptor*);
extern void destroy(Static17f20*);
struct Static17f20 {
    void* value;
    Static17f20() { construct(this, &descriptor); }
    ~Static17f20() { destroy(this); }
};
