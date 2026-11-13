// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2b80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2b80;
extern void construct(Statica2b80*, const Descriptor*);
extern void destroy(Statica2b80*);
struct Statica2b80 {
    void* value;
    Statica2b80() { construct(this, &descriptor); }
    ~Statica2b80() { destroy(this); }
};
