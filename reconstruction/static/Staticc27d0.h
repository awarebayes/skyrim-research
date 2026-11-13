// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc27d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc27d0;
extern void construct(Staticc27d0*, const Descriptor*);
extern void destroy(Staticc27d0*);
struct Staticc27d0 {
    void* value;
    Staticc27d0() { construct(this, &descriptor); }
    ~Staticc27d0() { destroy(this); }
};
