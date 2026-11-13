// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1af20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1af20;
extern void construct(Static1af20*, const Descriptor*);
extern void destroy(Static1af20*);
struct Static1af20 {
    void* value;
    Static1af20() { construct(this, &descriptor); }
    ~Static1af20() { destroy(this); }
};
