// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1add0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1add0;
extern void construct(Static1add0*, const Descriptor*);
extern void destroy(Static1add0*);
struct Static1add0 {
    void* value;
    Static1add0() { construct(this, &descriptor); }
    ~Static1add0() { destroy(this); }
};
