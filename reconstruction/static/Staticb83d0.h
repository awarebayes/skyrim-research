// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb83d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb83d0;
extern void construct(Staticb83d0*, const Descriptor*);
extern void destroy(Staticb83d0*);
struct Staticb83d0 {
    void* value;
    Staticb83d0() { construct(this, &descriptor); }
    ~Staticb83d0() { destroy(this); }
};
