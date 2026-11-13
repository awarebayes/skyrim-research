// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fe80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fe80;
extern void construct(Static9fe80*, const Descriptor*);
extern void destroy(Static9fe80*);
struct Static9fe80 {
    void* value;
    Static9fe80() { construct(this, &descriptor); }
    ~Static9fe80() { destroy(this); }
};
