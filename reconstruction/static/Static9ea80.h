// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ea80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ea80;
extern void construct(Static9ea80*, const Descriptor*);
extern void destroy(Static9ea80*);
struct Static9ea80 {
    void* value;
    Static9ea80() { construct(this, &descriptor); }
    ~Static9ea80() { destroy(this); }
};
