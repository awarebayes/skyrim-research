// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefc70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefc70;
extern void construct(Staticefc70*, const Descriptor*);
extern void destroy(Staticefc70*);
struct Staticefc70 {
    void* value;
    Staticefc70() { construct(this, &descriptor); }
    ~Staticefc70() { destroy(this); }
};
