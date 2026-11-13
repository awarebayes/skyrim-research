// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8940, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8940;
extern void construct(Statice8940*, const Descriptor*);
extern void destroy(Statice8940*);
struct Statice8940 {
    void* value;
    Statice8940() { construct(this, &descriptor); }
    ~Statice8940() { destroy(this); }
};
