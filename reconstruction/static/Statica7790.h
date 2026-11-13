// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica7790, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica7790;
extern void construct(Statica7790*, const Descriptor*);
extern void destroy(Statica7790*);
struct Statica7790 {
    void* value;
    Statica7790() { construct(this, &descriptor); }
    ~Statica7790() { destroy(this); }
};
