// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticae220, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticae220;
extern void construct(Staticae220*, const Descriptor*);
extern void destroy(Staticae220*);
struct Staticae220 {
    void* value;
    Staticae220() { construct(this, &descriptor); }
    ~Staticae220() { destroy(this); }
};
