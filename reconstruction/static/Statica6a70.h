// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6a70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6a70;
extern void construct(Statica6a70*, const Descriptor*);
extern void destroy(Statica6a70*);
struct Statica6a70 {
    void* value;
    Statica6a70() { construct(this, &descriptor); }
    ~Statica6a70() { destroy(this); }
};
