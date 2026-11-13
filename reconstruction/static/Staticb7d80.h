// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7d80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7d80;
extern void construct(Staticb7d80*, const Descriptor*);
extern void destroy(Staticb7d80*);
struct Staticb7d80 {
    void* value;
    Staticb7d80() { construct(this, &descriptor); }
    ~Staticb7d80() { destroy(this); }
};
