// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101050, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101050;
extern void construct(Static101050*, const Descriptor*);
extern void destroy(Static101050*);
struct Static101050 {
    void* value;
    Static101050() { construct(this, &descriptor); }
    ~Static101050() { destroy(this); }
};
