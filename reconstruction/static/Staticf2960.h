// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf2960, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf2960;
extern void construct(Staticf2960*, const Descriptor*);
extern void destroy(Staticf2960*);
struct Staticf2960 {
    void* value;
    Staticf2960() { construct(this, &descriptor); }
    ~Staticf2960() { destroy(this); }
};
