// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticdca0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticdca0;
extern void construct(Staticdca0*, const Descriptor*);
extern void destroy(Staticdca0*);
struct Staticdca0 {
    void* value;
    Staticdca0() { construct(this, &descriptor); }
    ~Staticdca0() { destroy(this); }
};
