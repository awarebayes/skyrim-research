// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1e310, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1e310;
extern void construct(Static1e310*, const Descriptor*);
extern void destroy(Static1e310*);
struct Static1e310 {
    void* value;
    Static1e310() { construct(this, &descriptor); }
    ~Static1e310() { destroy(this); }
};
