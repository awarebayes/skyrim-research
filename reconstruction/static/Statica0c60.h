// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0c60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0c60;
extern void construct(Statica0c60*, const Descriptor*);
extern void destroy(Statica0c60*);
struct Statica0c60 {
    void* value;
    Statica0c60() { construct(this, &descriptor); }
    ~Statica0c60() { destroy(this); }
};
