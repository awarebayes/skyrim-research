// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5780, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5780;
extern void construct(Staticc5780*, const Descriptor*);
extern void destroy(Staticc5780*);
struct Staticc5780 {
    void* value;
    Staticc5780() { construct(this, &descriptor); }
    ~Staticc5780() { destroy(this); }
};
