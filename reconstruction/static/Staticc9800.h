// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9800, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9800;
extern void construct(Staticc9800*, const Descriptor*);
extern void destroy(Staticc9800*);
struct Staticc9800 {
    void* value;
    Staticc9800() { construct(this, &descriptor); }
    ~Staticc9800() { destroy(this); }
};
