// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef1a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef1a0;
extern void construct(Staticef1a0*, const Descriptor*);
extern void destroy(Staticef1a0*);
struct Staticef1a0 {
    void* value;
    Staticef1a0() { construct(this, &descriptor); }
    ~Staticef1a0() { destroy(this); }
};
