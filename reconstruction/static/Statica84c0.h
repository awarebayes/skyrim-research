// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica84c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica84c0;
extern void construct(Statica84c0*, const Descriptor*);
extern void destroy(Statica84c0*);
struct Statica84c0 {
    void* value;
    Statica84c0() { construct(this, &descriptor); }
    ~Statica84c0() { destroy(this); }
};
