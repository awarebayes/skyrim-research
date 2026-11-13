// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc2650, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc2650;
extern void construct(Staticc2650*, const Descriptor*);
extern void destroy(Staticc2650*);
struct Staticc2650 {
    void* value;
    Staticc2650() { construct(this, &descriptor); }
    ~Staticc2650() { destroy(this); }
};
