// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice86f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice86f0;
extern void construct(Statice86f0*, const Descriptor*);
extern void destroy(Statice86f0*);
struct Statice86f0 {
    void* value;
    Statice86f0() { construct(this, &descriptor); }
    ~Statice86f0() { destroy(this); }
};
