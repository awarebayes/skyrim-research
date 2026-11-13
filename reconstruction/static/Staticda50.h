// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticda50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticda50;
extern void construct(Staticda50*, const Descriptor*);
extern void destroy(Staticda50*);
struct Staticda50 {
    void* value;
    Staticda50() { construct(this, &descriptor); }
    ~Staticda50() { destroy(this); }
};
