// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fe20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fe20;
extern void construct(Static9fe20*, const Descriptor*);
extern void destroy(Static9fe20*);
struct Static9fe20 {
    void* value;
    Static9fe20() { construct(this, &descriptor); }
    ~Static9fe20() { destroy(this); }
};
