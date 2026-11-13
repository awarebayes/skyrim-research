// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1dcb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1dcb0;
extern void construct(Static1dcb0*, const Descriptor*);
extern void destroy(Static1dcb0*);
struct Static1dcb0 {
    void* value;
    Static1dcb0() { construct(this, &descriptor); }
    ~Static1dcb0() { destroy(this); }
};
