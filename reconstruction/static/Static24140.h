// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24140, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24140;
extern void construct(Static24140*, const Descriptor*);
extern void destroy(Static24140*);
struct Static24140 {
    void* value;
    Static24140() { construct(this, &descriptor); }
    ~Static24140() { destroy(this); }
};
