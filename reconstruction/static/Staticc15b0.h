// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc15b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc15b0;
extern void construct(Staticc15b0*, const Descriptor*);
extern void destroy(Staticc15b0*);
struct Staticc15b0 {
    void* value;
    Staticc15b0() { construct(this, &descriptor); }
    ~Staticc15b0() { destroy(this); }
};
