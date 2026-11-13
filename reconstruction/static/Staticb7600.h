// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7600, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7600;
extern void construct(Staticb7600*, const Descriptor*);
extern void destroy(Staticb7600*);
struct Staticb7600 {
    void* value;
    Staticb7600() { construct(this, &descriptor); }
    ~Staticb7600() { destroy(this); }
};
