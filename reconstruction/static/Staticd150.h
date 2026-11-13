// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd150, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd150;
extern void construct(Staticd150*, const Descriptor*);
extern void destroy(Staticd150*);
struct Staticd150 {
    void* value;
    Staticd150() { construct(this, &descriptor); }
    ~Staticd150() { destroy(this); }
};
