// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2970, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2970;
extern void construct(Statica2970*, const Descriptor*);
extern void destroy(Statica2970*);
struct Statica2970 {
    void* value;
    Statica2970() { construct(this, &descriptor); }
    ~Statica2970() { destroy(this); }
};
