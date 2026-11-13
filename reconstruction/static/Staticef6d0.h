// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef6d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef6d0;
extern void construct(Staticef6d0*, const Descriptor*);
extern void destroy(Staticef6d0*);
struct Staticef6d0 {
    void* value;
    Staticef6d0() { construct(this, &descriptor); }
    ~Staticef6d0() { destroy(this); }
};
