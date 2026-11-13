// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica7b30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica7b30;
extern void construct(Statica7b30*, const Descriptor*);
extern void destroy(Statica7b30*);
struct Statica7b30 {
    void* value;
    Statica7b30() { construct(this, &descriptor); }
    ~Statica7b30() { destroy(this); }
};
