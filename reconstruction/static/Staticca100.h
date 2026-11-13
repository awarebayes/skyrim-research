// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca100, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca100;
extern void construct(Staticca100*, const Descriptor*);
extern void destroy(Staticca100*);
struct Staticca100 {
    void* value;
    Staticca100() { construct(this, &descriptor); }
    ~Staticca100() { destroy(this); }
};
