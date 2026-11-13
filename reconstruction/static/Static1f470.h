// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1f470, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1f470;
extern void construct(Static1f470*, const Descriptor*);
extern void destroy(Static1f470*);
struct Static1f470 {
    void* value;
    Static1f470() { construct(this, &descriptor); }
    ~Static1f470() { destroy(this); }
};
