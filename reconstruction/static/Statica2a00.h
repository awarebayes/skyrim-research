// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2a00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2a00;
extern void construct(Statica2a00*, const Descriptor*);
extern void destroy(Statica2a00*);
struct Statica2a00 {
    void* value;
    Statica2a00() { construct(this, &descriptor); }
    ~Statica2a00() { destroy(this); }
};
