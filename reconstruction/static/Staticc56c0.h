// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc56c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc56c0;
extern void construct(Staticc56c0*, const Descriptor*);
extern void destroy(Staticc56c0*);
struct Staticc56c0 {
    void* value;
    Staticc56c0() { construct(this, &descriptor); }
    ~Staticc56c0() { destroy(this); }
};
