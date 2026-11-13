// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica31d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica31d0;
extern void construct(Statica31d0*, const Descriptor*);
extern void destroy(Statica31d0*);
struct Statica31d0 {
    void* value;
    Statica31d0() { construct(this, &descriptor); }
    ~Statica31d0() { destroy(this); }
};
