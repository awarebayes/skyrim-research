// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1da40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1da40;
extern void construct(Static1da40*, const Descriptor*);
extern void destroy(Static1da40*);
struct Static1da40 {
    void* value;
    Static1da40() { construct(this, &descriptor); }
    ~Static1da40() { destroy(this); }
};
