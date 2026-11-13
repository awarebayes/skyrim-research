// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5330, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5330;
extern void construct(Staticc5330*, const Descriptor*);
extern void destroy(Staticc5330*);
struct Staticc5330 {
    void* value;
    Staticc5330() { construct(this, &descriptor); }
    ~Staticc5330() { destroy(this); }
};
