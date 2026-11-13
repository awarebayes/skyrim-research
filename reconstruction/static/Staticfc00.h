// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticfc00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticfc00;
extern void construct(Staticfc00*, const Descriptor*);
extern void destroy(Staticfc00*);
struct Staticfc00 {
    void* value;
    Staticfc00() { construct(this, &descriptor); }
    ~Staticfc00() { destroy(this); }
};
