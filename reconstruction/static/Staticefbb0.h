// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefbb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefbb0;
extern void construct(Staticefbb0*, const Descriptor*);
extern void destroy(Staticefbb0*);
struct Staticefbb0 {
    void* value;
    Staticefbb0() { construct(this, &descriptor); }
    ~Staticefbb0() { destroy(this); }
};
