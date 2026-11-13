// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefbe0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefbe0;
extern void construct(Staticefbe0*, const Descriptor*);
extern void destroy(Staticefbe0*);
struct Staticefbe0 {
    void* value;
    Staticefbe0() { construct(this, &descriptor); }
    ~Staticefbe0() { destroy(this); }
};
