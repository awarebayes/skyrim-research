// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9ce0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9ce0;
extern void construct(Staticc9ce0*, const Descriptor*);
extern void destroy(Staticc9ce0*);
struct Staticc9ce0 {
    void* value;
    Staticc9ce0() { construct(this, &descriptor); }
    ~Staticc9ce0() { destroy(this); }
};
