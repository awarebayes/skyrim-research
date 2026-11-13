// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0d80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0d80;
extern void construct(Statica0d80*, const Descriptor*);
extern void destroy(Statica0d80*);
struct Statica0d80 {
    void* value;
    Statica0d80() { construct(this, &descriptor); }
    ~Statica0d80() { destroy(this); }
};
