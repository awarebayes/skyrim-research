// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb90c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb90c0;
extern void construct(Staticb90c0*, const Descriptor*);
extern void destroy(Staticb90c0*);
struct Staticb90c0 {
    void* value;
    Staticb90c0() { construct(this, &descriptor); }
    ~Staticb90c0() { destroy(this); }
};
