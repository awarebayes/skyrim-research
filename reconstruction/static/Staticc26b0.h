// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc26b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc26b0;
extern void construct(Staticc26b0*, const Descriptor*);
extern void destroy(Staticc26b0*);
struct Staticc26b0 {
    void* value;
    Staticc26b0() { construct(this, &descriptor); }
    ~Staticc26b0() { destroy(this); }
};
