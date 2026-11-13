// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101110, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101110;
extern void construct(Static101110*, const Descriptor*);
extern void destroy(Static101110*);
struct Static101110 {
    void* value;
    Static101110() { construct(this, &descriptor); }
    ~Static101110() { destroy(this); }
};
