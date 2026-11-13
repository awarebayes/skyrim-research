// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3830, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3830;
extern void construct(Statica3830*, const Descriptor*);
extern void destroy(Statica3830*);
struct Statica3830 {
    void* value;
    Statica3830() { construct(this, &descriptor); }
    ~Statica3830() { destroy(this); }
};
