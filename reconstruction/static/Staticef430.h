// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef430, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef430;
extern void construct(Staticef430*, const Descriptor*);
extern void destroy(Staticef430*);
struct Staticef430 {
    void* value;
    Staticef430() { construct(this, &descriptor); }
    ~Staticef430() { destroy(this); }
};
