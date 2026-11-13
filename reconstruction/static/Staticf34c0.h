// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf34c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf34c0;
extern void construct(Staticf34c0*, const Descriptor*);
extern void destroy(Staticf34c0*);
struct Staticf34c0 {
    void* value;
    Staticf34c0() { construct(this, &descriptor); }
    ~Staticf34c0() { destroy(this); }
};
