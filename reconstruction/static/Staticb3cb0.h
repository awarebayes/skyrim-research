// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3cb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3cb0;
extern void construct(Staticb3cb0*, const Descriptor*);
extern void destroy(Staticb3cb0*);
struct Staticb3cb0 {
    void* value;
    Staticb3cb0() { construct(this, &descriptor); }
    ~Staticb3cb0() { destroy(this); }
};
