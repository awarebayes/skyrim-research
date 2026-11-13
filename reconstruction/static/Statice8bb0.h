// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8bb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8bb0;
extern void construct(Statice8bb0*, const Descriptor*);
extern void destroy(Statice8bb0*);
struct Statice8bb0 {
    void* value;
    Statice8bb0() { construct(this, &descriptor); }
    ~Statice8bb0() { destroy(this); }
};
