// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1dc80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1dc80;
extern void construct(Static1dc80*, const Descriptor*);
extern void destroy(Static1dc80*);
struct Static1dc80 {
    void* value;
    Static1dc80() { construct(this, &descriptor); }
    ~Static1dc80() { destroy(this); }
};
