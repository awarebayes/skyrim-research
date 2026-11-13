// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6590, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6590;
extern void construct(Statica6590*, const Descriptor*);
extern void destroy(Statica6590*);
struct Statica6590 {
    void* value;
    Statica6590() { construct(this, &descriptor); }
    ~Statica6590() { destroy(this); }
};
