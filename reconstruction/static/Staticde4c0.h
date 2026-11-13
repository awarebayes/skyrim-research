// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticde4c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticde4c0;
extern void construct(Staticde4c0*, const Descriptor*);
extern void destroy(Staticde4c0*);
struct Staticde4c0 {
    void* value;
    Staticde4c0() { construct(this, &descriptor); }
    ~Staticde4c0() { destroy(this); }
};
