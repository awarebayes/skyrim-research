// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb71e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb71e0;
extern void construct(Staticb71e0*, const Descriptor*);
extern void destroy(Staticb71e0*);
struct Staticb71e0 {
    void* value;
    Staticb71e0() { construct(this, &descriptor); }
    ~Staticb71e0() { destroy(this); }
};
