// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9f20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9f20;
extern void construct(Staticc9f20*, const Descriptor*);
extern void destroy(Staticc9f20*);
struct Staticc9f20 {
    void* value;
    Staticc9f20() { construct(this, &descriptor); }
    ~Staticc9f20() { destroy(this); }
};
