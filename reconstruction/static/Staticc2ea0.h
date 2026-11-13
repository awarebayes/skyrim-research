// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc2ea0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc2ea0;
extern void construct(Staticc2ea0*, const Descriptor*);
extern void destroy(Staticc2ea0*);
struct Staticc2ea0 {
    void* value;
    Staticc2ea0() { construct(this, &descriptor); }
    ~Staticc2ea0() { destroy(this); }
};
