// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static217f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static217f0;
extern void construct(Static217f0*, const Descriptor*);
extern void destroy(Static217f0*);
struct Static217f0 {
    void* value;
    Static217f0() { construct(this, &descriptor); }
    ~Static217f0() { destroy(this); }
};
