// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5750, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5750;
extern void construct(Staticc5750*, const Descriptor*);
extern void destroy(Staticc5750*);
struct Staticc5750 {
    void* value;
    Staticc5750() { construct(this, &descriptor); }
    ~Staticc5750() { destroy(this); }
};
