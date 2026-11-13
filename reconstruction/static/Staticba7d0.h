// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticba7d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticba7d0;
extern void construct(Staticba7d0*, const Descriptor*);
extern void destroy(Staticba7d0*);
struct Staticba7d0 {
    void* value;
    Staticba7d0() { construct(this, &descriptor); }
    ~Staticba7d0() { destroy(this); }
};
