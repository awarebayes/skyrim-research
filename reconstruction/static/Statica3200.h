// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3200, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3200;
extern void construct(Statica3200*, const Descriptor*);
extern void destroy(Statica3200*);
struct Statica3200 {
    void* value;
    Statica3200() { construct(this, &descriptor); }
    ~Statica3200() { destroy(this); }
};
