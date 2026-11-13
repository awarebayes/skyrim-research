// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static185a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static185a0;
extern void construct(Static185a0*, const Descriptor*);
extern void destroy(Static185a0*);
struct Static185a0 {
    void* value;
    Static185a0() { construct(this, &descriptor); }
    ~Static185a0() { destroy(this); }
};
