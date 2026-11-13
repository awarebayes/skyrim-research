// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice85a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice85a0;
extern void construct(Statice85a0*, const Descriptor*);
extern void destroy(Statice85a0*);
struct Statice85a0 {
    void* value;
    Statice85a0() { construct(this, &descriptor); }
    ~Statice85a0() { destroy(this); }
};
