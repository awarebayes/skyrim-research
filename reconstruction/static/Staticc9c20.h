// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9c20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9c20;
extern void construct(Staticc9c20*, const Descriptor*);
extern void destroy(Staticc9c20*);
struct Staticc9c20 {
    void* value;
    Staticc9c20() { construct(this, &descriptor); }
    ~Staticc9c20() { destroy(this); }
};
