// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3560, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3560;
extern void construct(Statica3560*, const Descriptor*);
extern void destroy(Statica3560*);
struct Statica3560 {
    void* value;
    Statica3560() { construct(this, &descriptor); }
    ~Statica3560() { destroy(this); }
};
