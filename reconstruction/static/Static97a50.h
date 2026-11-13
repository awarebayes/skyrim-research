// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97a50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97a50;
extern void construct(Static97a50*, const Descriptor*);
extern void destroy(Static97a50*);
struct Static97a50 {
    void* value;
    Static97a50() { construct(this, &descriptor); }
    ~Static97a50() { destroy(this); }
};
