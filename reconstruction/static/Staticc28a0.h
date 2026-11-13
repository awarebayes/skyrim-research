// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc28a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc28a0;
extern void construct(Staticc28a0*, const Descriptor*);
extern void destroy(Staticc28a0*);
struct Staticc28a0 {
    void* value;
    Staticc28a0() { construct(this, &descriptor); }
    ~Staticc28a0() { destroy(this); }
};
