// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1011a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1011a0;
extern void construct(Static1011a0*, const Descriptor*);
extern void destroy(Static1011a0*);
struct Static1011a0 {
    void* value;
    Static1011a0() { construct(this, &descriptor); }
    ~Static1011a0() { destroy(this); }
};
