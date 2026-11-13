// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9360, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9360;
extern void construct(Staticb9360*, const Descriptor*);
extern void destroy(Staticb9360*);
struct Staticb9360 {
    void* value;
    Staticb9360() { construct(this, &descriptor); }
    ~Staticb9360() { destroy(this); }
};
