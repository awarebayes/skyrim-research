// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf1c20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf1c20;
extern void construct(Staticf1c20*, const Descriptor*);
extern void destroy(Staticf1c20*);
struct Staticf1c20 {
    void* value;
    Staticf1c20() { construct(this, &descriptor); }
    ~Staticf1c20() { destroy(this); }
};
