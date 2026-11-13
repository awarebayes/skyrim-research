// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc1f30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc1f30;
extern void construct(Staticc1f30*, const Descriptor*);
extern void destroy(Staticc1f30*);
struct Staticc1f30 {
    void* value;
    Staticc1f30() { construct(this, &descriptor); }
    ~Staticc1f30() { destroy(this); }
};
