// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1e160, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1e160;
extern void construct(Static1e160*, const Descriptor*);
extern void destroy(Static1e160*);
struct Static1e160 {
    void* value;
    Static1e160() { construct(this, &descriptor); }
    ~Static1e160() { destroy(this); }
};
