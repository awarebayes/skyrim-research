// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24350, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24350;
extern void construct(Static24350*, const Descriptor*);
extern void destroy(Static24350*);
struct Static24350 {
    void* value;
    Static24350() { construct(this, &descriptor); }
    ~Static24350() { destroy(this); }
};
