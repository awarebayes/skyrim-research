// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static218e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static218e0;
extern void construct(Static218e0*, const Descriptor*);
extern void destroy(Static218e0*);
struct Static218e0 {
    void* value;
    Static218e0() { construct(this, &descriptor); }
    ~Static218e0() { destroy(this); }
};
