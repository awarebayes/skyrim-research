// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15730, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15730;
extern void construct(Static15730*, const Descriptor*);
extern void destroy(Static15730*);
struct Static15730 {
    void* value;
    Static15730() { construct(this, &descriptor); }
    ~Static15730() { destroy(this); }
};
