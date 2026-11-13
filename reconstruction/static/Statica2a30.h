// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2a30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2a30;
extern void construct(Statica2a30*, const Descriptor*);
extern void destroy(Statica2a30*);
struct Statica2a30 {
    void* value;
    Statica2a30() { construct(this, &descriptor); }
    ~Statica2a30() { destroy(this); }
};
