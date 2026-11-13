// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24080, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24080;
extern void construct(Static24080*, const Descriptor*);
extern void destroy(Static24080*);
struct Static24080 {
    void* value;
    Static24080() { construct(this, &descriptor); }
    ~Static24080() { destroy(this); }
};
