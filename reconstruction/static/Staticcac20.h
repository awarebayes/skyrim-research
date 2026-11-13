// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcac20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcac20;
extern void construct(Staticcac20*, const Descriptor*);
extern void destroy(Staticcac20*);
struct Staticcac20 {
    void* value;
    Staticcac20() { construct(this, &descriptor); }
    ~Staticcac20() { destroy(this); }
};
