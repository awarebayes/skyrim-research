// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static16230, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static16230;
extern void construct(Static16230*, const Descriptor*);
extern void destroy(Static16230*);
struct Static16230 {
    void* value;
    Static16230() { construct(this, &descriptor); }
    ~Static16230() { destroy(this); }
};
