// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97a80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97a80;
extern void construct(Static97a80*, const Descriptor*);
extern void destroy(Static97a80*);
struct Static97a80 {
    void* value;
    Static97a80() { construct(this, &descriptor); }
    ~Static97a80() { destroy(this); }
};
