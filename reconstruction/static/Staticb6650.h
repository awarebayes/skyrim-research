// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6650, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6650;
extern void construct(Staticb6650*, const Descriptor*);
extern void destroy(Staticb6650*);
struct Staticb6650 {
    void* value;
    Staticb6650() { construct(this, &descriptor); }
    ~Staticb6650() { destroy(this); }
};
