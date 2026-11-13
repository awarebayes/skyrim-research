// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static238b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static238b0;
extern void construct(Static238b0*, const Descriptor*);
extern void destroy(Static238b0*);
struct Static238b0 {
    void* value;
    Static238b0() { construct(this, &descriptor); }
    ~Static238b0() { destroy(this); }
};
