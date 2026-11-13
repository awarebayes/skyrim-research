// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101140, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101140;
extern void construct(Static101140*, const Descriptor*);
extern void destroy(Static101140*);
struct Static101140 {
    void* value;
    Static101140() { construct(this, &descriptor); }
    ~Static101140() { destroy(this); }
};
