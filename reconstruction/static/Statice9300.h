// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice9300, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice9300;
extern void construct(Statice9300*, const Descriptor*);
extern void destroy(Statice9300*);
struct Statice9300 {
    void* value;
    Statice9300() { construct(this, &descriptor); }
    ~Statice9300() { destroy(this); }
};
