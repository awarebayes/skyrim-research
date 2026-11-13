// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica7760, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica7760;
extern void construct(Statica7760*, const Descriptor*);
extern void destroy(Statica7760*);
struct Statica7760 {
    void* value;
    Statica7760() { construct(this, &descriptor); }
    ~Statica7760() { destroy(this); }
};
