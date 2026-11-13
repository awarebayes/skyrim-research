// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice9350, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice9350;
extern void construct(Statice9350*, const Descriptor*);
extern void destroy(Statice9350*);
struct Statice9350 {
    void* value;
    Statice9350() { construct(this, &descriptor); }
    ~Statice9350() { destroy(this); }
};
