// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static18070, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static18070;
extern void construct(Static18070*, const Descriptor*);
extern void destroy(Static18070*);
struct Static18070 {
    void* value;
    Static18070() { construct(this, &descriptor); }
    ~Static18070() { destroy(this); }
};
