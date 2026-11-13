// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca430, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca430;
extern void construct(Staticca430*, const Descriptor*);
extern void destroy(Staticca430*);
struct Staticca430 {
    void* value;
    Staticca430() { construct(this, &descriptor); }
    ~Staticca430() { destroy(this); }
};
