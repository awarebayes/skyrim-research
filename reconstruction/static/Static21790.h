// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21790, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21790;
extern void construct(Static21790*, const Descriptor*);
extern void destroy(Static21790*);
struct Static21790 {
    void* value;
    Static21790() { construct(this, &descriptor); }
    ~Static21790() { destroy(this); }
};
