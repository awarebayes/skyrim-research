// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb8df0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb8df0;
extern void construct(Staticb8df0*, const Descriptor*);
extern void destroy(Staticb8df0*);
struct Staticb8df0 {
    void* value;
    Staticb8df0() { construct(this, &descriptor); }
    ~Staticb8df0() { destroy(this); }
};
