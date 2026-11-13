// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3800, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3800;
extern void construct(Statica3800*, const Descriptor*);
extern void destroy(Statica3800*);
struct Statica3800 {
    void* value;
    Statica3800() { construct(this, &descriptor); }
    ~Statica3800() { destroy(this); }
};
