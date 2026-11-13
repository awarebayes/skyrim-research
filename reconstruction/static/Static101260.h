// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101260, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101260;
extern void construct(Static101260*, const Descriptor*);
extern void destroy(Static101260*);
struct Static101260 {
    void* value;
    Static101260() { construct(this, &descriptor); }
    ~Static101260() { destroy(this); }
};
