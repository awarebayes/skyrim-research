// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9810, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9810;
extern void construct(Staticb9810*, const Descriptor*);
extern void destroy(Staticb9810*);
struct Staticb9810 {
    void* value;
    Staticb9810() { construct(this, &descriptor); }
    ~Staticb9810() { destroy(this); }
};
