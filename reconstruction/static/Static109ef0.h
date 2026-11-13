// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109ef0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109ef0;
extern void construct(Static109ef0*, const Descriptor*);
extern void destroy(Static109ef0*);
struct Static109ef0 {
    void* value;
    Static109ef0() { construct(this, &descriptor); }
    ~Static109ef0() { destroy(this); }
};
