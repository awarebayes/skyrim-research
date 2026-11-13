// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static14e60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static14e60;
extern void construct(Static14e60*, const Descriptor*);
extern void destroy(Static14e60*);
struct Static14e60 {
    void* value;
    Static14e60() { construct(this, &descriptor); }
    ~Static14e60() { destroy(this); }
};
