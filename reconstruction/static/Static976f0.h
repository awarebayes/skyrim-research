// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static976f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static976f0;
extern void construct(Static976f0*, const Descriptor*);
extern void destroy(Static976f0*);
struct Static976f0 {
    void* value;
    Static976f0() { construct(this, &descriptor); }
    ~Static976f0() { destroy(this); }
};
