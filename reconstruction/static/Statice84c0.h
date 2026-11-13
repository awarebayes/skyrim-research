// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice84c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice84c0;
extern void construct(Statice84c0*, const Descriptor*);
extern void destroy(Statice84c0*);
struct Statice84c0 {
    void* value;
    Statice84c0() { construct(this, &descriptor); }
    ~Statice84c0() { destroy(this); }
};
