// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef700, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef700;
extern void construct(Staticef700*, const Descriptor*);
extern void destroy(Staticef700*);
struct Staticef700 {
    void* value;
    Staticef700() { construct(this, &descriptor); }
    ~Staticef700() { destroy(this); }
};
