// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc2800, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc2800;
extern void construct(Staticc2800*, const Descriptor*);
extern void destroy(Staticc2800*);
struct Staticc2800 {
    void* value;
    Staticc2800() { construct(this, &descriptor); }
    ~Staticc2800() { destroy(this); }
};
