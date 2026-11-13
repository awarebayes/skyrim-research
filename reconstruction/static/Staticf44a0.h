// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf44a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf44a0;
extern void construct(Staticf44a0*, const Descriptor*);
extern void destroy(Staticf44a0*);
struct Staticf44a0 {
    void* value;
    Staticf44a0() { construct(this, &descriptor); }
    ~Staticf44a0() { destroy(this); }
};
