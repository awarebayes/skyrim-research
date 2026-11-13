// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9b60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9b60;
extern void construct(Staticc9b60*, const Descriptor*);
extern void destroy(Staticc9b60*);
struct Staticc9b60 {
    void* value;
    Staticc9b60() { construct(this, &descriptor); }
    ~Staticc9b60() { destroy(this); }
};
