// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcadc0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcadc0;
extern void construct(Staticcadc0*, const Descriptor*);
extern void destroy(Staticcadc0*);
struct Staticcadc0 {
    void* value;
    Staticcadc0() { construct(this, &descriptor); }
    ~Staticcadc0() { destroy(this); }
};
