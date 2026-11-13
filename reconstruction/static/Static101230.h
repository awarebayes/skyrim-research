// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101230, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101230;
extern void construct(Static101230*, const Descriptor*);
extern void destroy(Static101230*);
struct Static101230 {
    void* value;
    Static101230() { construct(this, &descriptor); }
    ~Static101230() { destroy(this); }
};
