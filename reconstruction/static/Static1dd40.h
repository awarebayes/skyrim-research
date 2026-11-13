// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1dd40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1dd40;
extern void construct(Static1dd40*, const Descriptor*);
extern void destroy(Static1dd40*);
struct Static1dd40 {
    void* value;
    Static1dd40() { construct(this, &descriptor); }
    ~Static1dd40() { destroy(this); }
};
