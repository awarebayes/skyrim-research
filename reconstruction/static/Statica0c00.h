// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0c00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0c00;
extern void construct(Statica0c00*, const Descriptor*);
extern void destroy(Statica0c00*);
struct Statica0c00 {
    void* value;
    Statica0c00() { construct(this, &descriptor); }
    ~Statica0c00() { destroy(this); }
};
