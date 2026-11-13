// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8a30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8a30;
extern void construct(Statice8a30*, const Descriptor*);
extern void destroy(Statice8a30*);
struct Statice8a30 {
    void* value;
    Statice8a30() { construct(this, &descriptor); }
    ~Statice8a30() { destroy(this); }
};
