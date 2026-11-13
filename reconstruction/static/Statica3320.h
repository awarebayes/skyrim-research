// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3320, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3320;
extern void construct(Statica3320*, const Descriptor*);
extern void destroy(Statica3320*);
struct Statica3320 {
    void* value;
    Statica3320() { construct(this, &descriptor); }
    ~Statica3320() { destroy(this); }
};
