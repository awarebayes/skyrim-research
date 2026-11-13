// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2880, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2880;
extern void construct(Statica2880*, const Descriptor*);
extern void destroy(Statica2880*);
struct Statica2880 {
    void* value;
    Statica2880() { construct(this, &descriptor); }
    ~Statica2880() { destroy(this); }
};
