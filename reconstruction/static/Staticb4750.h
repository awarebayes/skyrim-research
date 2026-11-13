// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4750, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4750;
extern void construct(Staticb4750*, const Descriptor*);
extern void destroy(Staticb4750*);
struct Staticb4750 {
    void* value;
    Staticb4750() { construct(this, &descriptor); }
    ~Staticb4750() { destroy(this); }
};
