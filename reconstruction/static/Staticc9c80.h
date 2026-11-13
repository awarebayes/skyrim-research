// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9c80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9c80;
extern void construct(Staticc9c80*, const Descriptor*);
extern void destroy(Staticc9c80*);
struct Staticc9c80 {
    void* value;
    Staticc9c80() { construct(this, &descriptor); }
    ~Staticc9c80() { destroy(this); }
};
