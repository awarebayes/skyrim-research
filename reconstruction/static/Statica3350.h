// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3350, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3350;
extern void construct(Statica3350*, const Descriptor*);
extern void destroy(Statica3350*);
struct Statica3350 {
    void* value;
    Statica3350() { construct(this, &descriptor); }
    ~Statica3350() { destroy(this); }
};
