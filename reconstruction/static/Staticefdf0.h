// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefdf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefdf0;
extern void construct(Staticefdf0*, const Descriptor*);
extern void destroy(Staticefdf0*);
struct Staticefdf0 {
    void* value;
    Staticefdf0() { construct(this, &descriptor); }
    ~Staticefdf0() { destroy(this); }
};
