// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103130, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103130;
extern void construct(Static103130*, const Descriptor*);
extern void destroy(Static103130*);
struct Static103130 {
    void* value;
    Static103130() { construct(this, &descriptor); }
    ~Static103130() { destroy(this); }
};
