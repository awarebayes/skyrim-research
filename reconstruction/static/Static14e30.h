// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static14e30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static14e30;
extern void construct(Static14e30*, const Descriptor*);
extern void destroy(Static14e30*);
struct Static14e30 {
    void* value;
    Static14e30() { construct(this, &descriptor); }
    ~Static14e30() { destroy(this); }
};
