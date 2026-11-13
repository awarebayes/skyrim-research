// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9ec0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9ec0;
extern void construct(Staticc9ec0*, const Descriptor*);
extern void destroy(Staticc9ec0*);
struct Staticc9ec0 {
    void* value;
    Staticc9ec0() { construct(this, &descriptor); }
    ~Staticc9ec0() { destroy(this); }
};
