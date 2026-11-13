// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97660, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97660;
extern void construct(Static97660*, const Descriptor*);
extern void destroy(Static97660*);
struct Static97660 {
    void* value;
    Static97660() { construct(this, &descriptor); }
    ~Static97660() { destroy(this); }
};
