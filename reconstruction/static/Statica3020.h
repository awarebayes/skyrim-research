// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3020, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3020;
extern void construct(Statica3020*, const Descriptor*);
extern void destroy(Statica3020*);
struct Statica3020 {
    void* value;
    Statica3020() { construct(this, &descriptor); }
    ~Statica3020() { destroy(this); }
};
