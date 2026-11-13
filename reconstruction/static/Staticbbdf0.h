// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbbdf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbbdf0;
extern void construct(Staticbbdf0*, const Descriptor*);
extern void destroy(Staticbbdf0*);
struct Staticbbdf0 {
    void* value;
    Staticbbdf0() { construct(this, &descriptor); }
    ~Staticbbdf0() { destroy(this); }
};
