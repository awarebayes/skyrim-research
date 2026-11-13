// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd330, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd330;
extern void construct(Staticd330*, const Descriptor*);
extern void destroy(Staticd330*);
struct Staticd330 {
    void* value;
    Staticd330() { construct(this, &descriptor); }
    ~Staticd330() { destroy(this); }
};
