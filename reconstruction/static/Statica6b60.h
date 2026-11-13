// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6b60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6b60;
extern void construct(Statica6b60*, const Descriptor*);
extern void destroy(Statica6b60*);
struct Statica6b60 {
    void* value;
    Statica6b60() { construct(this, &descriptor); }
    ~Statica6b60() { destroy(this); }
};
