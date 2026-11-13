// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static101410, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static101410;
extern void construct(Static101410*, const Descriptor*);
extern void destroy(Static101410*);
struct Static101410 {
    void* value;
    Static101410() { construct(this, &descriptor); }
    ~Static101410() { destroy(this); }
};
