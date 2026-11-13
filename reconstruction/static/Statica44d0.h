// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica44d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica44d0;
extern void construct(Statica44d0*, const Descriptor*);
extern void destroy(Statica44d0*);
struct Statica44d0 {
    void* value;
    Statica44d0() { construct(this, &descriptor); }
    ~Statica44d0() { destroy(this); }
};
