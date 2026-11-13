// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0b70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0b70;
extern void construct(Statica0b70*, const Descriptor*);
extern void destroy(Statica0b70*);
struct Statica0b70 {
    void* value;
    Statica0b70() { construct(this, &descriptor); }
    ~Statica0b70() { destroy(this); }
};
