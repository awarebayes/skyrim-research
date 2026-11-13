// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8c00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8c00;
extern void construct(Statice8c00*, const Descriptor*);
extern void destroy(Statice8c00*);
struct Statice8c00 {
    void* value;
    Statice8c00() { construct(this, &descriptor); }
    ~Statice8c00() { destroy(this); }
};
