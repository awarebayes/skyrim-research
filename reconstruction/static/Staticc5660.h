// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5660, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5660;
extern void construct(Staticc5660*, const Descriptor*);
extern void destroy(Staticc5660*);
struct Staticc5660 {
    void* value;
    Staticc5660() { construct(this, &descriptor); }
    ~Staticc5660() { destroy(this); }
};
