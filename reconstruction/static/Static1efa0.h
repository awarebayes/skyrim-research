// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1efa0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1efa0;
extern void construct(Static1efa0*, const Descriptor*);
extern void destroy(Static1efa0*);
struct Static1efa0 {
    void* value;
    Static1efa0() { construct(this, &descriptor); }
    ~Static1efa0() { destroy(this); }
};
