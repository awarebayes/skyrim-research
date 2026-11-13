// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3080, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3080;
extern void construct(Statica3080*, const Descriptor*);
extern void destroy(Statica3080*);
struct Statica3080 {
    void* value;
    Statica3080() { construct(this, &descriptor); }
    ~Statica3080() { destroy(this); }
};
