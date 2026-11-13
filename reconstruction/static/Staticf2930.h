// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf2930, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf2930;
extern void construct(Staticf2930*, const Descriptor*);
extern void destroy(Staticf2930*);
struct Staticf2930 {
    void* value;
    Staticf2930() { construct(this, &descriptor); }
    ~Staticf2930() { destroy(this); }
};
