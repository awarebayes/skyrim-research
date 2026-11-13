// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8b80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8b80;
extern void construct(Statice8b80*, const Descriptor*);
extern void destroy(Statice8b80*);
struct Statice8b80 {
    void* value;
    Statice8b80() { construct(this, &descriptor); }
    ~Statice8b80() { destroy(this); }
};
