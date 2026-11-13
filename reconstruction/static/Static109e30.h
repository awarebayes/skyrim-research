// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109e30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109e30;
extern void construct(Static109e30*, const Descriptor*);
extern void destroy(Static109e30*);
struct Static109e30 {
    void* value;
    Static109e30() { construct(this, &descriptor); }
    ~Static109e30() { destroy(this); }
};
