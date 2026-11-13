// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101470, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101470;
extern void construct(Static101470*, const Descriptor*);
extern void destroy(Static101470*);
struct Static101470 {
    void* value;
    Static101470() { construct(this, &descriptor); }
    ~Static101470() { destroy(this); }
};
