// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3440, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3440;
extern void construct(Statica3440*, const Descriptor*);
extern void destroy(Statica3440*);
struct Statica3440 {
    void* value;
    Statica3440() { construct(this, &descriptor); }
    ~Statica3440() { destroy(this); }
};
