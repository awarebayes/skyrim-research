// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7ea0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7ea0;
extern void construct(Staticb7ea0*, const Descriptor*);
extern void destroy(Staticb7ea0*);
struct Staticb7ea0 {
    void* value;
    Staticb7ea0() { construct(this, &descriptor); }
    ~Staticb7ea0() { destroy(this); }
};
