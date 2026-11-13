// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97c30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97c30;
extern void construct(Static97c30*, const Descriptor*);
extern void destroy(Static97c30*);
struct Static97c30 {
    void* value;
    Static97c30() { construct(this, &descriptor); }
    ~Static97c30() { destroy(this); }
};
