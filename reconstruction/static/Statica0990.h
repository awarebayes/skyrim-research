// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica0990, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica0990;
extern void construct(Statica0990*, const Descriptor*);
extern void destroy(Statica0990*);
struct Statica0990 {
    void* value;
    Statica0990() { construct(this, &descriptor); }
    ~Statica0990() { destroy(this); }
};
