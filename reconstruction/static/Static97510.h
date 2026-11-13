// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97510, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97510;
extern void construct(Static97510*, const Descriptor*);
extern void destroy(Static97510*);
struct Static97510 {
    void* value;
    Static97510() { construct(this, &descriptor); }
    ~Static97510() { destroy(this); }
};
