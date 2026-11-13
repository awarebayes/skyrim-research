// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3740, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3740;
extern void construct(Statica3740*, const Descriptor*);
extern void destroy(Statica3740*);
struct Statica3740 {
    void* value;
    Statica3740() { construct(this, &descriptor); }
    ~Statica3740() { destroy(this); }
};
