// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2820, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2820;
extern void construct(Statica2820*, const Descriptor*);
extern void destroy(Statica2820*);
struct Statica2820 {
    void* value;
    Statica2820() { construct(this, &descriptor); }
    ~Statica2820() { destroy(this); }
};
