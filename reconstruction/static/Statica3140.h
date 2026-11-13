// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3140, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3140;
extern void construct(Statica3140*, const Descriptor*);
extern void destroy(Statica3140*);
struct Statica3140 {
    void* value;
    Statica3140() { construct(this, &descriptor); }
    ~Statica3140() { destroy(this); }
};
