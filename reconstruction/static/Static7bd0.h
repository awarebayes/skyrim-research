// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static7bd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static7bd0;
extern void construct(Static7bd0*, const Descriptor*);
extern void destroy(Static7bd0*);
struct Static7bd0 {
    void* value;
    Static7bd0() { construct(this, &descriptor); }
    ~Static7bd0() { destroy(this); }
};
