// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb330, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb330;
extern void construct(Staticbb330*, const Descriptor*);
extern void destroy(Staticbb330*);
struct Staticbb330 {
    void* value;
    Staticbb330() { construct(this, &descriptor); }
    ~Staticbb330() { destroy(this); }
};
