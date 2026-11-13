// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108420, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108420;
extern void construct(Static108420*, const Descriptor*);
extern void destroy(Static108420*);
struct Static108420 {
    void* value;
    Static108420() { construct(this, &descriptor); }
    ~Static108420() { destroy(this); }
};
