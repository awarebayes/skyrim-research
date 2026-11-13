// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbe300, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbe300;
extern void construct(Staticbe300*, const Descriptor*);
extern void destroy(Staticbe300*);
struct Staticbe300 {
    void* value;
    Staticbe300() { construct(this, &descriptor); }
    ~Staticbe300() { destroy(this); }
};
