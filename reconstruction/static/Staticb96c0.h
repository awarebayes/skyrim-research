// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb96c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb96c0;
extern void construct(Staticb96c0*, const Descriptor*);
extern void destroy(Staticb96c0*);
struct Staticb96c0 {
    void* value;
    Staticb96c0() { construct(this, &descriptor); }
    ~Staticb96c0() { destroy(this); }
};
