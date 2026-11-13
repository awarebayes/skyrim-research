// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109e00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109e00;
extern void construct(Static109e00*, const Descriptor*);
extern void destroy(Static109e00*);
struct Static109e00 {
    void* value;
    Static109e00() { construct(this, &descriptor); }
    ~Static109e00() { destroy(this); }
};
