// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica09c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica09c0;
extern void construct(Statica09c0*, const Descriptor*);
extern void destroy(Statica09c0*);
struct Statica09c0 {
    void* value;
    Statica09c0() { construct(this, &descriptor); }
    ~Statica09c0() { destroy(this); }
};
