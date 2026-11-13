// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica7b60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica7b60;
extern void construct(Statica7b60*, const Descriptor*);
extern void destroy(Statica7b60*);
struct Statica7b60 {
    void* value;
    Statica7b60() { construct(this, &descriptor); }
    ~Statica7b60() { destroy(this); }
};
