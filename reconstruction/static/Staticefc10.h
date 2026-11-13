// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefc10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefc10;
extern void construct(Staticefc10*, const Descriptor*);
extern void destroy(Staticefc10*);
struct Staticefc10 {
    void* value;
    Staticefc10() { construct(this, &descriptor); }
    ~Staticefc10() { destroy(this); }
};
