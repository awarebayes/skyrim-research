// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1c470, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1c470;
extern void construct(Static1c470*, const Descriptor*);
extern void destroy(Static1c470*);
struct Static1c470 {
    void* value;
    Static1c470() { construct(this, &descriptor); }
    ~Static1c470() { destroy(this); }
};
