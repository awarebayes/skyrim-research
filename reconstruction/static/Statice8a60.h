// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8a60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8a60;
extern void construct(Statice8a60*, const Descriptor*);
extern void destroy(Statice8a60*);
struct Statice8a60 {
    void* value;
    Statice8a60() { construct(this, &descriptor); }
    ~Statice8a60() { destroy(this); }
};
