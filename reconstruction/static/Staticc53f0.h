// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc53f0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc53f0;
extern void construct(Staticc53f0*, const Descriptor*);
extern void destroy(Staticc53f0*);
struct Staticc53f0 {
    void* value;
    Staticc53f0() { construct(this, &descriptor); }
    ~Staticc53f0() { destroy(this); }
};
