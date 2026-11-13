// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97b70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97b70;
extern void construct(Static97b70*, const Descriptor*);
extern void destroy(Static97b70*);
struct Static97b70 {
    void* value;
    Static97b70() { construct(this, &descriptor); }
    ~Static97b70() { destroy(this); }
};
