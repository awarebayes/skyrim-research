// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2f00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2f00;
extern void construct(Statica2f00*, const Descriptor*);
extern void destroy(Statica2f00*);
struct Statica2f00 {
    void* value;
    Statica2f00() { construct(this, &descriptor); }
    ~Statica2f00() { destroy(this); }
};
