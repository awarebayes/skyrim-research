// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb68f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb68f0;
extern void construct(Staticb68f0*, const Descriptor*);
extern void destroy(Staticb68f0*);
struct Staticb68f0 {
    void* value;
    Staticb68f0() { construct(this, &descriptor); }
    ~Staticb68f0() { destroy(this); }
};
