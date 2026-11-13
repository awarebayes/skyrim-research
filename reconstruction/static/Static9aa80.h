// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9aa80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9aa80;
extern void construct(Static9aa80*, const Descriptor*);
extern void destroy(Static9aa80*);
struct Static9aa80 {
    void* value;
    Static9aa80() { construct(this, &descriptor); }
    ~Static9aa80() { destroy(this); }
};
