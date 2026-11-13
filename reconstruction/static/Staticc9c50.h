// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9c50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9c50;
extern void construct(Staticc9c50*, const Descriptor*);
extern void destroy(Staticc9c50*);
struct Staticc9c50 {
    void* value;
    Staticc9c50() { construct(this, &descriptor); }
    ~Staticc9c50() { destroy(this); }
};
