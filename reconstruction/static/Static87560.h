// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static87560, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static87560;
extern void construct(Static87560*, const Descriptor*);
extern void destroy(Static87560*);
struct Static87560 {
    void* value;
    Static87560() { construct(this, &descriptor); }
    ~Static87560() { destroy(this); }
};
