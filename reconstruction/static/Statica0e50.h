// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0e50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0e50;
extern void construct(Statica0e50*, const Descriptor*);
extern void destroy(Statica0e50*);
struct Statica0e50 {
    void* value;
    Statica0e50() { construct(this, &descriptor); }
    ~Statica0e50() { destroy(this); }
};
