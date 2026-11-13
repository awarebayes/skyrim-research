// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1035e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1035e0;
extern void construct(Static1035e0*, const Descriptor*);
extern void destroy(Static1035e0*);
struct Static1035e0 {
    void* value;
    Static1035e0() { construct(this, &descriptor); }
    ~Static1035e0() { destroy(this); }
};
