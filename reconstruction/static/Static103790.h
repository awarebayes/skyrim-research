// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103790, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103790;
extern void construct(Static103790*, const Descriptor*);
extern void destroy(Static103790*);
struct Static103790 {
    void* value;
    Static103790() { construct(this, &descriptor); }
    ~Static103790() { destroy(this); }
};
