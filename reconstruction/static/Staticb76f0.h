// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb76f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb76f0;
extern void construct(Staticb76f0*, const Descriptor*);
extern void destroy(Staticb76f0*);
struct Staticb76f0 {
    void* value;
    Staticb76f0() { construct(this, &descriptor); }
    ~Staticb76f0() { destroy(this); }
};
