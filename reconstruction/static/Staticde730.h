// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticde730, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticde730;
extern void construct(Staticde730*, const Descriptor*);
extern void destroy(Staticde730*);
struct Staticde730 {
    void* value;
    Staticde730() { construct(this, &descriptor); }
    ~Staticde730() { destroy(this); }
};
