// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109bc0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109bc0;
extern void construct(Static109bc0*, const Descriptor*);
extern void destroy(Static109bc0*);
struct Static109bc0 {
    void* value;
    Static109bc0() { construct(this, &descriptor); }
    ~Static109bc0() { destroy(this); }
};
