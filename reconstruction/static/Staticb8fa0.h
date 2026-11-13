// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb8fa0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb8fa0;
extern void construct(Staticb8fa0*, const Descriptor*);
extern void destroy(Staticb8fa0*);
struct Staticb8fa0 {
    void* value;
    Staticb8fa0() { construct(this, &descriptor); }
    ~Staticb8fa0() { destroy(this); }
};
