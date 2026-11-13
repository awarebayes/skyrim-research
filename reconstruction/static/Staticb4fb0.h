// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4fb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4fb0;
extern void construct(Staticb4fb0*, const Descriptor*);
extern void destroy(Staticb4fb0*);
struct Staticb4fb0 {
    void* value;
    Staticb4fb0() { construct(this, &descriptor); }
    ~Staticb4fb0() { destroy(this); }
};
