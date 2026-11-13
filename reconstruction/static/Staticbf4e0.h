// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbf4e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbf4e0;
extern void construct(Staticbf4e0*, const Descriptor*);
extern void destroy(Staticbf4e0*);
struct Staticbf4e0 {
    void* value;
    Staticbf4e0() { construct(this, &descriptor); }
    ~Staticbf4e0() { destroy(this); }
};
