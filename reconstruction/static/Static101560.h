// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101560, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101560;
extern void construct(Static101560*, const Descriptor*);
extern void destroy(Static101560*);
struct Static101560 {
    void* value;
    Static101560() { construct(this, &descriptor); }
    ~Static101560() { destroy(this); }
};
