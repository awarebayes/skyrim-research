// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9d10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9d10;
extern void construct(Staticc9d10*, const Descriptor*);
extern void destroy(Staticc9d10*);
struct Staticc9d10 {
    void* value;
    Staticc9d10() { construct(this, &descriptor); }
    ~Staticc9d10() { destroy(this); }
};
