// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefdc0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefdc0;
extern void construct(Staticefdc0*, const Descriptor*);
extern void destroy(Staticefdc0*);
struct Staticefdc0 {
    void* value;
    Staticefdc0() { construct(this, &descriptor); }
    ~Staticefdc0() { destroy(this); }
};
