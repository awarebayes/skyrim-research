// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97b40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97b40;
extern void construct(Static97b40*, const Descriptor*);
extern void destroy(Static97b40*);
struct Static97b40 {
    void* value;
    Static97b40() { construct(this, &descriptor); }
    ~Static97b40() { destroy(this); }
};
