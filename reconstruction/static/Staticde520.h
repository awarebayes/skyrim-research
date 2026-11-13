// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticde520, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticde520;
extern void construct(Staticde520*, const Descriptor*);
extern void destroy(Staticde520*);
struct Staticde520 {
    void* value;
    Staticde520() { construct(this, &descriptor); }
    ~Staticde520() { destroy(this); }
};
