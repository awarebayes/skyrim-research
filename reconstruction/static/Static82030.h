// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static82030, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static82030;
extern void construct(Static82030*, const Descriptor*);
extern void destroy(Static82030*);
struct Static82030 {
    void* value;
    Static82030() { construct(this, &descriptor); }
    ~Static82030() { destroy(this); }
};
