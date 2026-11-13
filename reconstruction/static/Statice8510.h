// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8510, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8510;
extern void construct(Statice8510*, const Descriptor*);
extern void destroy(Statice8510*);
struct Statice8510 {
    void* value;
    Statice8510() { construct(this, &descriptor); }
    ~Statice8510() { destroy(this); }
};
