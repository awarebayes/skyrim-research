// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3290, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3290;
extern void construct(Statica3290*, const Descriptor*);
extern void destroy(Statica3290*);
struct Statica3290 {
    void* value;
    Statica3290() { construct(this, &descriptor); }
    ~Statica3290() { destroy(this); }
};
