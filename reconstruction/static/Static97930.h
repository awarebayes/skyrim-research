// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97930, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97930;
extern void construct(Static97930*, const Descriptor*);
extern void destroy(Static97930*);
struct Static97930 {
    void* value;
    Static97930() { construct(this, &descriptor); }
    ~Static97930() { destroy(this); }
};
