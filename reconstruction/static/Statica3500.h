// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3500, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3500;
extern void construct(Statica3500*, const Descriptor*);
extern void destroy(Statica3500*);
struct Statica3500 {
    void* value;
    Statica3500() { construct(this, &descriptor); }
    ~Statica3500() { destroy(this); }
};
