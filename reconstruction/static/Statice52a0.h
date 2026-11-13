// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice52a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice52a0;
extern void construct(Statice52a0*, const Descriptor*);
extern void destroy(Statice52a0*);
struct Statice52a0 {
    void* value;
    Statice52a0() { construct(this, &descriptor); }
    ~Statice52a0() { destroy(this); }
};
