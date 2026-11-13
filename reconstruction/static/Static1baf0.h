// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1baf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1baf0;
extern void construct(Static1baf0*, const Descriptor*);
extern void destroy(Static1baf0*);
struct Static1baf0 {
    void* value;
    Static1baf0() { construct(this, &descriptor); }
    ~Static1baf0() { destroy(this); }
};
