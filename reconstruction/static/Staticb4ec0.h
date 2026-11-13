// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4ec0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4ec0;
extern void construct(Staticb4ec0*, const Descriptor*);
extern void destroy(Staticb4ec0*);
struct Staticb4ec0 {
    void* value;
    Staticb4ec0() { construct(this, &descriptor); }
    ~Staticb4ec0() { destroy(this); }
};
