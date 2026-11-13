// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica160, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica160;
extern void construct(Statica160*, const Descriptor*);
extern void destroy(Statica160*);
struct Statica160 {
    void* value;
    Statica160() { construct(this, &descriptor); }
    ~Statica160() { destroy(this); }
};
