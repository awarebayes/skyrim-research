// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108510, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108510;
extern void construct(Static108510*, const Descriptor*);
extern void destroy(Static108510*);
struct Static108510 {
    void* value;
    Static108510() { construct(this, &descriptor); }
    ~Static108510() { destroy(this); }
};
