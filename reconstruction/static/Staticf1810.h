// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf1810, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf1810;
extern void construct(Staticf1810*, const Descriptor*);
extern void destroy(Staticf1810*);
struct Staticf1810 {
    void* value;
    Staticf1810() { construct(this, &descriptor); }
    ~Staticf1810() { destroy(this); }
};
