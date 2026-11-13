// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7120, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7120;
extern void construct(Staticb7120*, const Descriptor*);
extern void destroy(Staticb7120*);
struct Staticb7120 {
    void* value;
    Staticb7120() { construct(this, &descriptor); }
    ~Staticb7120() { destroy(this); }
};
