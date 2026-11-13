// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15010, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15010;
extern void construct(Static15010*, const Descriptor*);
extern void destroy(Static15010*);
struct Static15010 {
    void* value;
    Static15010() { construct(this, &descriptor); }
    ~Static15010() { destroy(this); }
};
