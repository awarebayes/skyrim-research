// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7510, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7510;
extern void construct(Staticb7510*, const Descriptor*);
extern void destroy(Staticb7510*);
struct Staticb7510 {
    void* value;
    Staticb7510() { construct(this, &descriptor); }
    ~Staticb7510() { destroy(this); }
};
