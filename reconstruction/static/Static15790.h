// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15790, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15790;
extern void construct(Static15790*, const Descriptor*);
extern void destroy(Static15790*);
struct Static15790 {
    void* value;
    Static15790() { construct(this, &descriptor); }
    ~Static15790() { destroy(this); }
};
