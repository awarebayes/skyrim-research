// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3860, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3860;
extern void construct(Statica3860*, const Descriptor*);
extern void destroy(Statica3860*);
struct Statica3860 {
    void* value;
    Statica3860() { construct(this, &descriptor); }
    ~Statica3860() { destroy(this); }
};
