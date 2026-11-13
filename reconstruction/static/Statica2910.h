// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2910, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2910;
extern void construct(Statica2910*, const Descriptor*);
extern void destroy(Statica2910*);
struct Statica2910 {
    void* value;
    Statica2910() { construct(this, &descriptor); }
    ~Statica2910() { destroy(this); }
};
