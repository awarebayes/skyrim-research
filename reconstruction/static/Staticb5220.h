// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5220, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5220;
extern void construct(Staticb5220*, const Descriptor*);
extern void destroy(Staticb5220*);
struct Staticb5220 {
    void* value;
    Staticb5220() { construct(this, &descriptor); }
    ~Staticb5220() { destroy(this); }
};
