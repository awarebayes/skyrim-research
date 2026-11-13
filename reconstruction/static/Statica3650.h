// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3650, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3650;
extern void construct(Statica3650*, const Descriptor*);
extern void destroy(Statica3650*);
struct Statica3650 {
    void* value;
    Statica3650() { construct(this, &descriptor); }
    ~Statica3650() { destroy(this); }
};
