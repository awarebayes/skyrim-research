// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static14f20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static14f20;
extern void construct(Static14f20*, const Descriptor*);
extern void destroy(Static14f20*);
struct Static14f20 {
    void* value;
    Static14f20() { construct(this, &descriptor); }
    ~Static14f20() { destroy(this); }
};
