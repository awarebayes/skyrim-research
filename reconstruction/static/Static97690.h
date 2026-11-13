// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97690, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97690;
extern void construct(Static97690*, const Descriptor*);
extern void destroy(Static97690*);
struct Static97690 {
    void* value;
    Static97690() { construct(this, &descriptor); }
    ~Static97690() { destroy(this); }
};
