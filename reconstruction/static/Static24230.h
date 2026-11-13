// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static24230, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static24230;
extern void construct(Static24230*, const Descriptor*);
extern void destroy(Static24230*);
struct Static24230 {
    void* value;
    Static24230() { construct(this, &descriptor); }
    ~Static24230() { destroy(this); }
};
