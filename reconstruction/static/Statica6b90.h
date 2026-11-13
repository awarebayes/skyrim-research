// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6b90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6b90;
extern void construct(Statica6b90*, const Descriptor*);
extern void destroy(Statica6b90*);
struct Statica6b90 {
    void* value;
    Statica6b90() { construct(this, &descriptor); }
    ~Statica6b90() { destroy(this); }
};
