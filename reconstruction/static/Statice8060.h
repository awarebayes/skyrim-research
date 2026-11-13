// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice8060, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice8060;
extern void construct(Statice8060*, const Descriptor*);
extern void destroy(Statice8060*);
struct Statice8060 {
    void* value;
    Statice8060() { construct(this, &descriptor); }
    ~Statice8060() { destroy(this); }
};
