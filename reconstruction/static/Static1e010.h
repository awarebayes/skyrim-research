// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1e010, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1e010;
extern void construct(Static1e010*, const Descriptor*);
extern void destroy(Static1e010*);
struct Static1e010 {
    void* value;
    Static1e010() { construct(this, &descriptor); }
    ~Static1e010() { destroy(this); }
};
