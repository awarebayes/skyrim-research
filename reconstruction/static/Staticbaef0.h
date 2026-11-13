// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbaef0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbaef0;
extern void construct(Staticbaef0*, const Descriptor*);
extern void destroy(Staticbaef0*);
struct Staticbaef0 {
    void* value;
    Staticbaef0() { construct(this, &descriptor); }
    ~Staticbaef0() { destroy(this); }
};
