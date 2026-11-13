// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7330, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7330;
extern void construct(Staticb7330*, const Descriptor*);
extern void destroy(Staticb7330*);
struct Staticb7330 {
    void* value;
    Staticb7330() { construct(this, &descriptor); }
    ~Staticb7330() { destroy(this); }
};
