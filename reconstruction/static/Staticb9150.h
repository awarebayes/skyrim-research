// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9150, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9150;
extern void construct(Staticb9150*, const Descriptor*);
extern void destroy(Staticb9150*);
struct Staticb9150 {
    void* value;
    Staticb9150() { construct(this, &descriptor); }
    ~Staticb9150() { destroy(this); }
};
