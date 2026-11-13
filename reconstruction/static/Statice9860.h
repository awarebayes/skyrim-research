// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice9860, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice9860;
extern void construct(Statice9860*, const Descriptor*);
extern void destroy(Statice9860*);
struct Statice9860 {
    void* value;
    Statice9860() { construct(this, &descriptor); }
    ~Statice9860() { destroy(this); }
};
