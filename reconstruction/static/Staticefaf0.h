// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefaf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefaf0;
extern void construct(Staticefaf0*, const Descriptor*);
extern void destroy(Staticefaf0*);
struct Staticefaf0 {
    void* value;
    Staticefaf0() { construct(this, &descriptor); }
    ~Staticefaf0() { destroy(this); }
};
