// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf660, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf660;
extern void construct(Staticf660*, const Descriptor*);
extern void destroy(Staticf660*);
struct Staticf660 {
    void* value;
    Staticf660() { construct(this, &descriptor); }
    ~Staticf660() { destroy(this); }
};
