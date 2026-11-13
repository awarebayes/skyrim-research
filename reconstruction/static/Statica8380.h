// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica8380, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica8380;
extern void construct(Statica8380*, const Descriptor*);
extern void destroy(Statica8380*);
struct Statica8380 {
    void* value;
    Statica8380() { construct(this, &descriptor); }
    ~Statica8380() { destroy(this); }
};
