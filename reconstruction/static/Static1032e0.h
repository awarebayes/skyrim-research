// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1032e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1032e0;
extern void construct(Static1032e0*, const Descriptor*);
extern void destroy(Static1032e0*);
struct Static1032e0 {
    void* value;
    Static1032e0() { construct(this, &descriptor); }
    ~Static1032e0() { destroy(this); }
};
