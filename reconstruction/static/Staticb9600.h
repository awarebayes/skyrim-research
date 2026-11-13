// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9600, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9600;
extern void construct(Staticb9600*, const Descriptor*);
extern void destroy(Staticb9600*);
struct Staticb9600 {
    void* value;
    Staticb9600() { construct(this, &descriptor); }
    ~Staticb9600() { destroy(this); }
};
