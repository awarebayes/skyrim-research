// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice98d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice98d0;
extern void construct(Statice98d0*, const Descriptor*);
extern void destroy(Statice98d0*);
struct Statice98d0 {
    void* value;
    Statice98d0() { construct(this, &descriptor); }
    ~Statice98d0() { destroy(this); }
};
