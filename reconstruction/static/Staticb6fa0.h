// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6fa0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6fa0;
extern void construct(Staticb6fa0*, const Descriptor*);
extern void destroy(Staticb6fa0*);
struct Staticb6fa0 {
    void* value;
    Staticb6fa0() { construct(this, &descriptor); }
    ~Staticb6fa0() { destroy(this); }
};
