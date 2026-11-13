// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1e130, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1e130;
extern void construct(Static1e130*, const Descriptor*);
extern void destroy(Static1e130*);
struct Static1e130 {
    void* value;
    Static1e130() { construct(this, &descriptor); }
    ~Static1e130() { destroy(this); }
};
