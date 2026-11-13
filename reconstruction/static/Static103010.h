// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103010, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103010;
extern void construct(Static103010*, const Descriptor*);
extern void destroy(Static103010*);
struct Static103010 {
    void* value;
    Static103010() { construct(this, &descriptor); }
    ~Static103010() { destroy(this); }
};
