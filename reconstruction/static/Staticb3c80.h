// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3c80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3c80;
extern void construct(Staticb3c80*, const Descriptor*);
extern void destroy(Staticb3c80*);
struct Staticb3c80 {
    void* value;
    Staticb3c80() { construct(this, &descriptor); }
    ~Staticb3c80() { destroy(this); }
};
