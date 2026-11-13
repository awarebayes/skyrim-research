// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice82b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice82b0;
extern void construct(Statice82b0*, const Descriptor*);
extern void destroy(Statice82b0*);
struct Statice82b0 {
    void* value;
    Statice82b0() { construct(this, &descriptor); }
    ~Statice82b0() { destroy(this); }
};
