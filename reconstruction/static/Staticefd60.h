// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefd60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefd60;
extern void construct(Staticefd60*, const Descriptor*);
extern void destroy(Staticefd60*);
struct Staticefd60 {
    void* value;
    Staticefd60() { construct(this, &descriptor); }
    ~Staticefd60() { destroy(this); }
};
