// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice730, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice730;
extern void construct(Statice730*, const Descriptor*);
extern void destroy(Statice730*);
struct Statice730 {
    void* value;
    Statice730() { construct(this, &descriptor); }
    ~Statice730() { destroy(this); }
};
