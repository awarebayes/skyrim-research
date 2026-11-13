// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0a80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0a80;
extern void construct(Statica0a80*, const Descriptor*);
extern void destroy(Statica0a80*);
struct Statica0a80 {
    void* value;
    Statica0a80() { construct(this, &descriptor); }
    ~Statica0a80() { destroy(this); }
};
