// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101620, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101620;
extern void construct(Static101620*, const Descriptor*);
extern void destroy(Static101620*);
struct Static101620 {
    void* value;
    Static101620() { construct(this, &descriptor); }
    ~Static101620() { destroy(this); }
};
