// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2850, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2850;
extern void construct(Statica2850*, const Descriptor*);
extern void destroy(Statica2850*);
struct Statica2850 {
    void* value;
    Statica2850() { construct(this, &descriptor); }
    ~Statica2850() { destroy(this); }
};
