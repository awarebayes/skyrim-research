// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9fb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9fb0;
extern void construct(Staticc9fb0*, const Descriptor*);
extern void destroy(Staticc9fb0*);
struct Staticc9fb0 {
    void* value;
    Staticc9fb0() { construct(this, &descriptor); }
    ~Staticc9fb0() { destroy(this); }
};
