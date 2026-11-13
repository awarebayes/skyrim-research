// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2e70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2e70;
extern void construct(Statica2e70*, const Descriptor*);
extern void destroy(Statica2e70*);
struct Statica2e70 {
    void* value;
    Statica2e70() { construct(this, &descriptor); }
    ~Statica2e70() { destroy(this); }
};
