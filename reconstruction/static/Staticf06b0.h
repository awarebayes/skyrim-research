// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf06b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf06b0;
extern void construct(Staticf06b0*, const Descriptor*);
extern void destroy(Staticf06b0*);
struct Staticf06b0 {
    void* value;
    Staticf06b0() { construct(this, &descriptor); }
    ~Staticf06b0() { destroy(this); }
};
