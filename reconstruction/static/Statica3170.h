// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3170, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3170;
extern void construct(Statica3170*, const Descriptor*);
extern void destroy(Statica3170*);
struct Statica3170 {
    void* value;
    Statica3170() { construct(this, &descriptor); }
    ~Statica3170() { destroy(this); }
};
