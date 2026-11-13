// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica35f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica35f0;
extern void construct(Statica35f0*, const Descriptor*);
extern void destroy(Statica35f0*);
struct Statica35f0 {
    void* value;
    Statica35f0() { construct(this, &descriptor); }
    ~Statica35f0() { destroy(this); }
};
