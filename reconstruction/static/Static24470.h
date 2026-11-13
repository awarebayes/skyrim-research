// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24470, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24470;
extern void construct(Static24470*, const Descriptor*);
extern void destroy(Static24470*);
struct Static24470 {
    void* value;
    Static24470() { construct(this, &descriptor); }
    ~Static24470() { destroy(this); }
};
