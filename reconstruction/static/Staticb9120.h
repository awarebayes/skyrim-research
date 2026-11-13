// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9120, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9120;
extern void construct(Staticb9120*, const Descriptor*);
extern void destroy(Staticb9120*);
struct Staticb9120 {
    void* value;
    Staticb9120() { construct(this, &descriptor); }
    ~Staticb9120() { destroy(this); }
};
