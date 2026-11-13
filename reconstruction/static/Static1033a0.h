// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1033a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1033a0;
extern void construct(Static1033a0*, const Descriptor*);
extern void destroy(Static1033a0*);
struct Static1033a0 {
    void* value;
    Static1033a0() { construct(this, &descriptor); }
    ~Static1033a0() { destroy(this); }
};
