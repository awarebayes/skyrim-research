// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6920, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6920;
extern void construct(Staticb6920*, const Descriptor*);
extern void destroy(Staticb6920*);
struct Staticb6920 {
    void* value;
    Staticb6920() { construct(this, &descriptor); }
    ~Staticb6920() { destroy(this); }
};
